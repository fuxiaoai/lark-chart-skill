#!/usr/bin/env python3
"""Lint SVG artifacts for freeform Lark whiteboard rendering."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
SKILL_ROOT = HERE.parent.parent
DEFAULT_TOKENS = SKILL_ROOT / "assets" / "style-tokens" / "_catalog.json"
STYLE_TOKENS_DIR = SKILL_ROOT / "assets" / "style-tokens"

COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}")
UNSUPPORTED_TAGS = {
    "filter",
    "radialGradient",
    "pattern",
    "clipPath",
    "mask",
    "foreignObject",
}
TEXT_REQUIRED_MODES = {"sankey", "roadmap", "prototype", "custom"}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def token_colors(path: Path) -> set[str]:
    data = load_json(path)
    colors: set[str] = set()

    def pull_palette(container: dict[str, Any]) -> None:
        for section in ("fill_colors", "border_colors", "text_colors"):
            for item in container.get(section) or []:
                value = item.get("value")
                if isinstance(value, str):
                    colors.add(value.lower())

    if "house_style" in data:
        pull_palette(data["house_style"])
    style = data.get("style") or {}
    palette = style.get("palette") or {}
    pull_palette(palette)
    return colors


def style_seed_colors(seed_id: str) -> set[str]:
    candidate = STYLE_TOKENS_DIR / f"{seed_id}.json"
    if not candidate.exists():
        raise FileNotFoundError(f"style-seed token not found: {candidate}")
    return token_colors(candidate)


def plan_budget_colors(plan_path: Path) -> tuple[set[str], list[str]]:
    """Read plan.json.style_budget; return (colors, notes).

    Accepts either a flat list of hex strings or the same shape as token files.
    """
    notes: list[str] = []
    if not plan_path.exists():
        notes.append(f"plan not found: {plan_path}; falling back to permissive validation")
        return set(), notes
    data = load_json(plan_path)
    budget = data.get("style_budget") or {}
    colors: set[str] = set()
    if isinstance(budget, list):
        for item in budget:
            if isinstance(item, str):
                m = COLOR_RE.findall(item)
                colors.update(c.lower() for c in m)
    elif isinstance(budget, dict):
        palette = budget.get("palette") or budget
        for section in ("fill_colors", "border_colors", "text_colors"):
            for item in palette.get(section) or []:
                value = item.get("value") if isinstance(item, dict) else item
                if isinstance(value, str):
                    m = COLOR_RE.findall(value)
                    colors.update(c.lower() for c in m)
        for key in ("colors", "allowed_colors"):
            for value in budget.get(key) or []:
                if isinstance(value, str):
                    m = COLOR_RE.findall(value)
                    colors.update(c.lower() for c in m)
    if not colors:
        notes.append(f"plan.style_budget has no colors; falling back to permissive validation")
    return colors, notes


def parse_svg(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    by_tag: dict[str, int] = {}
    roles: list[str] = []
    colors: set[str] = set()
    texts: list[str] = []
    unsupported: list[str] = []
    transforms: list[str] = []

    for el in root.iter():
        tag = local_name(el.tag)
        by_tag[tag] = by_tag.get(tag, 0) + 1
        if tag in UNSUPPORTED_TAGS:
            unsupported.append(tag)
        attrs = {local_name(k): str(v) for k, v in el.attrib.items()}
        role = attrs.get("data-role") or attrs.get("class") or ""
        if role:
            roles.append(role)
        if "transform" in attrs:
            transforms.append(attrs["transform"])
        for value in attrs.values():
            for color in COLOR_RE.findall(value):
                colors.add(color.lower())
        if tag == "text":
            text = "".join(el.itertext()).strip()
            if text:
                texts.append(text)

    role_blob = " ".join(roles)
    return {
        "by_tag": by_tag,
        "roles": roles,
        "role_blob": role_blob,
        "colors": sorted(colors),
        "texts": texts,
        "text_count": len(texts),
        "unsupported_tags": sorted(set(unsupported)),
        "has_title": by_tag.get("title", 0) > 0,
        "has_desc": by_tag.get("desc", 0) > 0,
        "rects": by_tag.get("rect", 0),
        "paths": by_tag.get("path", 0),
        "polylines": by_tag.get("polyline", 0),
        "lines": by_tag.get("line", 0),
        "circles": by_tag.get("circle", 0),
        "ellipses": by_tag.get("ellipse", 0),
        "polygons": by_tag.get("polygon", 0),
        "transforms": transforms,
        "role_counts": {
            "sankey_flow": role_blob.count("sankey-flow"),
            "roadmap_axis": role_blob.count("roadmap-axis"),
            "roadmap_track": role_blob.count("roadmap-track"),
            "roadmap_milestone": role_blob.count("roadmap-milestone"),
            "prototype_screen": role_blob.count("prototype-screen"),
            "prototype_surface": role_blob.count("prototype-surface"),
            "prototype_control": role_blob.count("prototype-control"),
            "landscape_layer": role_blob.count("landscape-layer"),
            "atmosphere": role_blob.count("atmosphere"),
            "hero_object": role_blob.count("hero-object"),
        },
    }


def unknown_colors(metrics: dict[str, Any], allowed: set[str]) -> list[str]:
    ignored = {"#000000"}
    return sorted(set(metrics["colors"]) - allowed - ignored)


def validate_common(metrics: dict[str, Any], allowed: set[str]) -> list[str]:
    failures: list[str] = []
    if metrics["unsupported_tags"]:
        failures.append("uses unsupported SVG tags: " + ", ".join(metrics["unsupported_tags"]))
    extra = unknown_colors(metrics, allowed)
    if extra:
        failures.append("uses colors outside token budget: " + ", ".join(extra))
    if not metrics["has_title"]:
        failures.append("missing <title>")
    if not metrics["has_desc"]:
        failures.append("missing <desc>")
    if not metrics["roles"]:
        failures.append("missing data-role markers for visual intent")
    for transform in metrics["transforms"]:
        if "skew" in transform or "matrix" in transform:
            failures.append(f"uses unstable transform: {transform}")
    return failures


def validate_mode(mode: str, metrics: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    roles = metrics["role_counts"]
    connectorish = metrics["paths"] + metrics["polylines"] + metrics["lines"]
    non_rect_shapes = metrics["paths"] + metrics["polylines"] + metrics["circles"] + metrics["ellipses"] + metrics["polygons"]

    if mode in TEXT_REQUIRED_MODES and metrics["text_count"] < 6:
        failures.append("too few text labels for an information graphic")

    if mode == "sankey":
        if roles["sankey_flow"] < 4:
            failures.append("sankey mode needs at least four data-role=sankey-flow paths")
        if connectorish < 6:
            failures.append("sankey mode needs enough flow/connector geometry")
        if metrics["text_count"] < 9:
            failures.append("sankey mode needs source, middle, and result labels")

    elif mode == "roadmap":
        if roles["roadmap_axis"] < 1:
            failures.append("roadmap mode needs a data-role=roadmap-axis")
        if roles["roadmap_track"] < 3:
            failures.append("roadmap mode needs at least three tracks or phases")
        if roles["roadmap_milestone"] < 5:
            failures.append("roadmap mode needs at least five milestones")

    elif mode == "prototype":
        if roles["prototype_screen"] < 1:
            failures.append("prototype mode needs a screen/device frame")
        if roles["prototype_surface"] < 3:
            failures.append("prototype mode needs at least three UI surfaces")
        if roles["prototype_control"] < 5:
            failures.append("prototype mode needs enough controls or UI states")

    elif mode == "illustration":
        if roles["landscape_layer"] < 5:
            failures.append("illustration mode needs at least five foreground/midground/background layers")
        if roles["atmosphere"] < 3:
            failures.append("illustration mode needs at least three atmosphere elements")
        if roles["hero_object"] < 1:
            failures.append("illustration mode needs a hero object")
        if non_rect_shapes < 10:
            failures.append("illustration mode is too rect-heavy or sparse")

    elif mode == "custom":
        if non_rect_shapes < 4 and connectorish < 4:
            failures.append("custom mode lacks visual structure beyond cards")

    else:
        failures.append(f"unknown mode: {mode}")

    if metrics["rects"] > 0 and non_rect_shapes / max(metrics["rects"], 1) < 0.25 and mode != "prototype":
        failures.append("output appears to regress into a rectangle card wall")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path)
    parser.add_argument(
        "--mode",
        choices=["sankey", "roadmap", "prototype", "illustration", "custom"],
        default="custom",
    )
    parser.add_argument(
        "--tokens",
        type=Path,
        default=DEFAULT_TOKENS,
        help="catalog/token JSON; used as fallback when --plan/--style-seed missing",
    )
    parser.add_argument(
        "--style-seed",
        dest="style_seed",
        default=None,
        help="token id under assets/style-tokens (e.g. milestone, system-architecture); merged into allowed palette",
    )
    parser.add_argument(
        "--plan",
        dest="plan",
        type=Path,
        default=None,
        help="plan.json path; if its style_budget has colors, those take precedence and seed/catalog only widen the set",
    )
    parser.add_argument(
        "--strict-budget",
        action="store_true",
        help="when set and --plan provides a non-empty style_budget, do NOT widen with seed/catalog",
    )
    args = parser.parse_args()

    notes: list[str] = []
    plan_colors: set[str] = set()
    if args.plan is not None:
        plan_colors, plan_notes = plan_budget_colors(args.plan)
        notes.extend(plan_notes)

    seed_colors: set[str] = set()
    if args.style_seed:
        try:
            seed_colors = style_seed_colors(args.style_seed)
        except FileNotFoundError as exc:
            notes.append(str(exc))

    catalog_colors = token_colors(args.tokens)

    if plan_colors and args.strict_budget:
        allowed = set(plan_colors)
        source = "plan.style_budget (strict)"
    elif plan_colors:
        allowed = plan_colors | seed_colors | catalog_colors
        source = "plan.style_budget ∪ style-seed ∪ catalog"
    elif seed_colors:
        allowed = seed_colors | catalog_colors
        source = "style-seed ∪ catalog"
        notes.append("plan missing or empty; using style-seed + catalog (permissive)")
    else:
        allowed = catalog_colors
        source = "catalog only"
        notes.append("plan and style-seed both missing; using catalog only (permissive)")

    metrics = parse_svg(args.svg)
    failures = validate_common(metrics, allowed) + validate_mode(args.mode, metrics)
    report = {
        "ok": not failures,
        "mode": args.mode,
        "artifact": str(args.svg),
        "palette_source": source,
        "allowed_color_count": len(allowed),
        "notes": notes,
        "metrics": metrics,
        "failures": failures,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
