#!/usr/bin/env python3
"""Extract style tokens from the reference whiteboards in assets/raw/.

For each reference board we emit a compact "style fingerprint" JSON that the
Planner can reference without ever seeing the full node dump. We deliberately
avoid exporting coordinates or node counts — the whole point is that style
tokens travel, layouts do not.

Per-board fingerprint:
    assets/style-tokens/<id>.json
Cross-board catalog (aggregates + ranked common tokens):
    assets/style-tokens/_catalog.json

Idempotent: rerunning overwrites both outputs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
SKILL_ROOT = HERE.parent.parent
DEFAULT_MANIFEST = SKILL_ROOT.parent.parent / "data" / "design-lark-chart" / "reference_boards.json"
DEFAULT_RAW_DIR = SKILL_ROOT / "assets" / "raw"
DEFAULT_OUT_DIR = SKILL_ROOT / "assets" / "style-tokens"


def _top(counter: Counter[Any], k: int = 16) -> list[dict[str, Any]]:
    items = [(v, c) for v, c in counter.most_common() if v not in (None, "", "#000000")]
    return [{"value": v, "count": c} for v, c in items[:k]]


def _safe(obj: dict[str, Any], *path: str, default: Any = None) -> Any:
    cur: Any = obj
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
        if cur is None:
            return default
    return cur


def fingerprint(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    fills, borders, border_widths, border_styles = Counter(), Counter(), Counter(), Counter()
    text_colors, font_sizes, font_weights, aligns = Counter(), Counter(), Counter(), Counter()
    shape_types = Counter()
    connector_shapes, arrow_styles, line_widths = Counter(), Counter(), Counter()
    has_inline_svg = False

    for n in nodes:
        t = n.get("type")
        if t == "composite_shape":
            shape_types[_safe(n, "composite_shape", "type")] += 1
            fills[_safe(n, "style", "fill_color")] += 1
            borders[_safe(n, "style", "border_color")] += 1
            border_widths[_safe(n, "style", "border_width")] += 1
            border_styles[_safe(n, "style", "border_style")] += 1
            text_colors[_safe(n, "text", "text_color")] += 1
            fs = _safe(n, "text", "font_size")
            if fs is not None:
                font_sizes[fs] += 1
            font_weights[_safe(n, "text", "font_weight")] += 1
            aligns[_safe(n, "text", "horizontal_align")] += 1
        elif t == "text_shape":
            text_colors[_safe(n, "text", "text_color")] += 1
            fs = _safe(n, "text", "font_size")
            if fs is not None:
                font_sizes[fs] += 1
            font_weights[_safe(n, "text", "font_weight")] += 1
            aligns[_safe(n, "text", "horizontal_align")] += 1
        elif t == "connector":
            connector_shapes[_safe(n, "connector", "shape")] += 1
            arrow_styles[_safe(n, "connector", "end", "arrow_style")] += 1
            line_widths[_safe(n, "style", "border_width")] += 1
            borders[_safe(n, "style", "border_color")] += 1
        elif t == "svg":
            has_inline_svg = True

    return {
        "palette": {
            "fill_colors": _top(fills),
            "border_colors": _top(borders),
            "text_colors": _top(text_colors),
        },
        "typography": {
            "font_sizes": _top(font_sizes),
            "font_weights": _top(font_weights),
            "horizontal_align": _top(aligns),
        },
        "shape": {
            "composite_types": _top(shape_types),
            "border_widths": _top(border_widths),
            "border_styles": _top(border_styles),
        },
        "connector": {
            "shapes": _top(connector_shapes),
            "arrow_styles": _top(arrow_styles),
            "line_widths": _top(line_widths),
        },
        "uses_inline_svg_decoration": has_inline_svg,
    }


def load_manifest(path: Path, raw_dir: Path, out_dir: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text())

    catalog_path = out_dir / "_catalog.json"
    catalog = json.loads(catalog_path.read_text()) if catalog_path.exists() else {}
    catalog_boards = catalog.get("boards") or []
    raw_ids = {p.stem for p in raw_dir.glob("*.json")}
    boards: list[dict[str, Any]] = []
    seen: set[str] = set()

    def append_board(bid: str, meta: dict[str, Any] | None = None) -> None:
        if bid in seen or bid not in raw_ids:
            return
        existing_path = out_dir / f"{bid}.json"
        existing = json.loads(existing_path.read_text()) if existing_path.exists() else {}
        meta = meta or {}
        boards.append({
            "id": bid,
            "cn": meta.get("cn") or existing.get("cn", bid),
            "use_case": meta.get("use_case") or existing.get("use_case", ""),
            "token": existing.get("source_token", ""),
        })
        seen.add(bid)

    for board in catalog_boards:
        append_board(board.get("id", ""), board)
    for bid in sorted(raw_ids):
        append_board(bid)
    return {"source_doc": catalog.get("source_doc"), "boards": boards}


def aggregate(per_board: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Rank values across all boards to surface the 'house style'."""
    agg: dict[str, Counter[Any]] = {
        "fill_colors": Counter(), "border_colors": Counter(), "text_colors": Counter(),
        "font_sizes": Counter(), "font_weights": Counter(),
        "composite_types": Counter(), "connector_shapes": Counter(), "arrow_styles": Counter(),
    }
    for fp in per_board.values():
        for item in fp["palette"]["fill_colors"]:     agg["fill_colors"][item["value"]]    += item["count"]
        for item in fp["palette"]["border_colors"]:   agg["border_colors"][item["value"]]  += item["count"]
        for item in fp["palette"]["text_colors"]:     agg["text_colors"][item["value"]]    += item["count"]
        for item in fp["typography"]["font_sizes"]:   agg["font_sizes"][item["value"]]     += item["count"]
        for item in fp["typography"]["font_weights"]: agg["font_weights"][item["value"]]   += item["count"]
        for item in fp["shape"]["composite_types"]:   agg["composite_types"][item["value"]] += item["count"]
        for item in fp["connector"]["shapes"]:        agg["connector_shapes"][item["value"]] += item["count"]
        for item in fp["connector"]["arrow_styles"]:  agg["arrow_styles"][item["value"]]   += item["count"]
    return {k: _top(v, k=12) for k, v in agg.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--raw-dir",  type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--out-dir",  type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    manifest = load_manifest(args.manifest, args.raw_dir, args.out_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    per_board: dict[str, dict[str, Any]] = {}
    for board in manifest["boards"]:
        bid = board["id"]
        raw_path = args.raw_dir / f"{bid}.json"
        if not raw_path.exists():
            print(f"[skip] {bid}: raw not found at {raw_path}", file=sys.stderr)
            continue
        raw = json.loads(raw_path.read_text())
        existing_path = args.out_dir / f"{bid}.json"
        existing = json.loads(existing_path.read_text()) if existing_path.exists() else {}
        fp = fingerprint(raw.get("nodes", []))
        fp_with_meta = {
            "id": bid,
            "cn": board["cn"],
            "use_case": board["use_case"],
            "source_token": board.get("token") or existing.get("source_token", ""),
            "node_count": len(raw.get("nodes", [])),
            "style": fp,
        }
        (args.out_dir / f"{bid}.json").write_text(
            json.dumps(fp_with_meta, ensure_ascii=False, indent=2)
        )
        per_board[bid] = fp
        print(f"[ok] {bid}: {len(raw['nodes'])} nodes -> style-tokens/{bid}.json")

    catalog = {
        "source_doc": manifest.get("source_doc"),
        "boards": [{"id": b["id"], "cn": b["cn"], "use_case": b["use_case"]} for b in manifest["boards"]],
        "house_style": aggregate(per_board),
    }
    (args.out_dir / "_catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2)
    )
    print(f"[ok] catalog: {args.out_dir / '_catalog.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
