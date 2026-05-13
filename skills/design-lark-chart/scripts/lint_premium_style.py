#!/usr/bin/env python3
"""Strict structural lint for premium visual chart routes."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve()
SKILL_ROOT = HERE.parent.parent
TOKENS_DIR = SKILL_ROOT / "assets" / "style-tokens"
CATALOG = TOKENS_DIR / "_catalog.json"
COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}")

CHART_TYPES = {"system-architecture", "matrix-quadrant", "sketch-architecture"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def token_colors(chart_type: str) -> set[str]:
    colors: set[str] = set()
    for path in (TOKENS_DIR / f"{chart_type}.json", CATALOG):
        data = load_json(path)
        style = data.get("style") or {}
        palette = style.get("palette") or {}
        for section in ("fill_colors", "border_colors", "text_colors"):
            for item in palette.get(section) or []:
                value = item.get("value")
                if isinstance(value, str):
                    colors.add(value.lower())
        house = data.get("house_style") or {}
        for section in ("fill_colors", "border_colors", "text_colors"):
            for item in house.get(section) or []:
                value = item.get("value")
                if isinstance(value, str):
                    colors.add(value.lower())
    return colors


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def attrs_text(attrs: dict[str, str]) -> str:
    return " ".join(str(value) for value in attrs.values())


def role(attrs: dict[str, str]) -> str:
    return attrs.get("data-role") or attrs.get("class") or ""


def collect_svg(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    elements = list(root.iter())
    by_tag: dict[str, int] = {}
    colors: set[str] = set()
    texts: list[str] = []
    roles: list[str] = []
    dashed = 0

    for el in elements:
        tag = local_name(el.tag)
        by_tag[tag] = by_tag.get(tag, 0) + 1
        attrs = {local_name(k): str(v) for k, v in el.attrib.items()}
        roles.append(role(attrs))
        for color in COLOR_RE.findall(attrs_text(attrs)):
            colors.add(color.lower())
        if "stroke-dasharray" in attrs or "dash" in attrs.get("style", ""):
            dashed += 1
        if tag == "text":
            text = "".join(el.itertext()).strip()
            if text:
                texts.append(text)

    connector_tags = {"line", "polyline", "path"}
    connectors = sum(by_tag.get(tag, 0) for tag in connector_tags)
    role_blob = " ".join(roles)
    text_blob = "\n".join(texts)

    return {
        "kind": "svg",
        "by_tag": by_tag,
        "colors": sorted(colors),
        "texts": texts,
        "text_blob": text_blob,
        "roles": roles,
        "role_blob": role_blob,
        "rects": by_tag.get("rect", 0),
        "texts_count": by_tag.get("text", 0),
        "connectors": connectors,
        "patterns": by_tag.get("pattern", 0),
        "dashed": dashed,
        "quadrants": role_blob.count("quadrant"),
        "axis_labels": role_blob.count("axis-label"),
        "section_zones": role_blob.count("section-zone"),
        "sketch_strokes": role_blob.count("sketch-stroke"),
        "sidebars": role_blob.count("sidebar"),
        "layer_labels": role_blob.count("layer-label"),
        "legends": role_blob.count("legend"),
    }


def walk(nodes: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for node in nodes:
        yield node
        children = node.get("children") or []
        if isinstance(children, list):
            yield from walk(children)


def collect_json(path: Path) -> dict[str, Any]:
    data = load_json(path)
    nodes = list(walk(data.get("nodes") or []))
    colors: set[str] = set()
    texts: list[str] = []
    dashed = 0
    connectors = 0

    for node in nodes:
        for key in ("fillColor", "borderColor", "textColor"):
            value = node.get(key)
            if isinstance(value, str):
                colors.add(value.lower())
        if isinstance(node.get("text"), str):
            texts.append(node["text"])
        if node.get("type") == "connector":
            connectors += 1
            connector = node.get("connector") or {}
            value = connector.get("lineColor")
            if isinstance(value, str):
                colors.add(value.lower())
        if node.get("borderStyle") == "dash":
            dashed += 1

    text_blob = "\n".join(texts)
    return {
        "kind": "json",
        "colors": sorted(colors),
        "texts": texts,
        "text_blob": text_blob,
        "rects": sum(1 for node in nodes if node.get("type") == "rect"),
        "frames": sum(1 for node in nodes if node.get("type") == "frame"),
        "texts_count": len(texts),
        "connectors": connectors,
        "patterns": 0,
        "dashed": dashed,
        "quadrants": sum(1 for text in texts if "/" in text and ("价值" in text or "复杂" in text or "成本" in text)),
        "axis_labels": sum(1 for text in texts if text in {"业务价值", "实施复杂度", "价值", "复杂度", "成本"}),
        "section_zones": dashed,
        "sketch_strokes": 0,
        "sidebars": sum(1 for text in texts if text in {"外部依赖", "Runtime", "可观测中心"}),
        "layer_labels": sum(1 for text in texts if text.endswith("层")),
        "legends": sum(1 for text in texts if text.startswith("P0") or text.startswith("P1")),
    }


def collect(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".svg":
        return collect_svg(path)
    if path.suffix.lower() == ".json":
        return collect_json(path)
    raise SystemExit(f"unsupported file type: {path.suffix}")


def unknown_colors(metrics: dict[str, Any], allowed: set[str]) -> list[str]:
    ignored = {"#000000"}
    return sorted(set(metrics["colors"]) - allowed - ignored)


def validate(chart_type: str, metrics: dict[str, Any], allowed: set[str]) -> list[str]:
    failures: list[str] = []
    extra_colors = unknown_colors(metrics, allowed)
    if extra_colors:
        failures.append(f"uses colors outside style tokens: {', '.join(extra_colors)}")
    if metrics["texts_count"] < 8:
        failures.append("too little text structure; output is likely decorative or incomplete")

    if chart_type == "system-architecture":
        if metrics["rects"] < 28:
            failures.append("system architecture needs dense service cards and containers")
        if metrics["patterns"] < 1:
            failures.append("missing subtle grid or texture background")
        if metrics["layer_labels"] < 3:
            failures.append("expected at least three layer labels")
        if metrics["sidebars"] < 1:
            failures.append("missing external dependency/runtime sidebar")
        if metrics["legends"] < 1:
            failures.append("missing legend or priority/status chips")
        if metrics["connectors"] < 5:
            failures.append("connector density is too low for system architecture")

    if chart_type == "matrix-quadrant":
        if metrics["quadrants"] < 4:
            failures.append("expected four explicit quadrant regions")
        if metrics["axis_labels"] < 2:
            failures.append("missing horizontal and vertical axis labels")
        if metrics["rects"] < 5:
            failures.append("matrix needs shared board plus four colored quadrant blocks")
        if "four-column" in metrics.get("role_blob", ""):
            failures.append("matrix appears to be four horizontal columns, not a 2x2 matrix")

    if chart_type == "sketch-architecture":
        if metrics["section_zones"] < 2:
            failures.append("expected at least two dashed section zones")
        if metrics["sketch_strokes"] < 8:
            failures.append("missing hand-drawn double lines or underline strokes")
        if metrics["rects"] < 8:
            failures.append("too few sketch cards")
        if metrics["connectors"] < 2:
            failures.append("missing key cross-stage connectors")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chart_type", choices=sorted(CHART_TYPES))
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()

    allowed = token_colors(args.chart_type)
    metrics = collect(args.artifact)
    failures = validate(args.chart_type, metrics, allowed)
    report = {
        "ok": not failures,
        "chart_type": args.chart_type,
        "artifact": str(args.artifact),
        "metrics": metrics,
        "failures": failures,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
