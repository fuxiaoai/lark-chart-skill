#!/usr/bin/env python3
"""Strict structural lint for lark-style-architecture DSL boards."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve()
SKILL_ROOT = HERE.parent.parent
DEFAULT_TOKENS = SKILL_ROOT / "assets" / "style-tokens" / "lark-style-architecture.json"


def walk(nodes: Iterable[dict[str, Any]], depth: int = 1) -> Iterable[tuple[dict[str, Any], int]]:
    for node in nodes:
        yield node, depth
        children = node.get("children") or []
        if isinstance(children, list):
            yield from walk(children, depth + 1)


def descendant_count(node: dict[str, Any], node_type: str) -> int:
    return sum(1 for child, _ in walk(node.get("children") or []) if child.get("type") == node_type)


def token_colors(tokens: dict[str, Any]) -> set[str]:
    style = tokens.get("style") or {}
    colors: set[str] = set()
    for section in ("fill_colors", "border_colors", "text_colors"):
        for item in ((style.get("palette") or {}).get(section) or []):
            value = item.get("value")
            if isinstance(value, str):
                colors.add(value.lower())
    return colors


def color_values(node: dict[str, Any]) -> Iterable[str]:
    for key in ("fillColor", "borderColor", "textColor"):
        value = node.get(key)
        if isinstance(value, str):
            yield value
    connector = node.get("connector") or {}
    value = connector.get("lineColor")
    if isinstance(value, str):
        yield value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("--tokens", type=Path, default=DEFAULT_TOKENS)
    args = parser.parse_args()

    board = json.loads(args.board.read_text())
    tokens = json.loads(args.tokens.read_text())
    allowed_colors = token_colors(tokens)
    nodes = list(walk(board.get("nodes") or []))

    frames = [node for node, _ in nodes if node.get("type") == "frame"]
    rects = [node for node, _ in nodes if node.get("type") == "rect"]
    connectors = [node for node, _ in nodes if node.get("type") == "connector"]
    max_depth = max((depth for _, depth in nodes), default=0)

    used_colors = {color.lower() for node, _ in nodes for color in color_values(node)}
    unknown_colors = sorted(used_colors - allowed_colors)
    nonwhite_fills = {
        node.get("fillColor", "").lower()
        for node in frames + rects
        if isinstance(node.get("fillColor"), str) and node.get("fillColor", "").lower() != "#ffffff"
    }
    module_frames = [
        node for node in frames
        if node.get("fillColor", "").lower() not in ("", "#ffffff", "#fbfcfd")
        and descendant_count(node, "rect") >= 3
    ]
    detail_cards = [
        node for node in rects
        if "\n" in str(node.get("text") or "") or int(node.get("height") or 0) >= 88
    ]
    filled_badges = [
        node for node in rects
        if node.get("fillColor", "").lower() not in ("", "#ffffff")
        and node.get("textColor", "").lower() == "#ffffff"
    ]

    right_angle = 0
    arrow_end = 0
    for connector_node in connectors:
        connector = connector_node.get("connector") or {}
        if connector.get("lineShape") == "rightAngle":
            right_angle += 1
        if connector.get("endArrow") == "arrow":
            arrow_end += 1

    min_connectors = max(5, math.ceil(max(len(rects), 1) / 6))
    failures: list[str] = []
    if unknown_colors:
        failures.append("uses colors outside lark-style-architecture style tokens")
    if len(rects) < 18:
        failures.append("too few rect nodes; output is likely a flat layer diagram")
    if len(frames) < 7:
        failures.append("too few frames; expected banner plus module containers")
    if max_depth < 4:
        failures.append("nesting is too shallow; expected modules with inner cards")
    if len(module_frames) < 4:
        failures.append("expected at least four colored module containers")
    if len(detail_cards) < 6:
        failures.append("expected multiple detail cards or bullet clusters inside modules")
    if len(nonwhite_fills) < 5:
        failures.append("palette is too flat; expected several semantic fills from the preview")
    if not filled_badges:
        failures.append("missing filled badge or terminal action highlight")
    if len(connectors) < min_connectors:
        failures.append("connector density is too low")
    if connectors and right_angle / len(connectors) < 0.8:
        failures.append("most connectors must use rightAngle")
    if connectors and arrow_end != len(connectors):
        failures.append("all lark-style connectors must end with arrow")

    report = {
        "ok": not failures,
        "metrics": {
            "frames": len(frames),
            "rects": len(rects),
            "connectors": len(connectors),
            "max_depth": max_depth,
            "module_frames": len(module_frames),
            "detail_cards": len(detail_cards),
            "nonwhite_fills": sorted(nonwhite_fills),
            "unknown_colors": unknown_colors,
            "right_angle_connectors": right_angle,
            "arrow_end_connectors": arrow_end,
        },
        "failures": failures,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
