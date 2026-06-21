#!/usr/bin/env python3
"""Validate a Draw.io .drawio file."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from xml.etree import ElementTree


def validate(path: Path) -> dict:
    try:
        root = ElementTree.fromstring(path.read_text(encoding="utf-8"))
    except ElementTree.ParseError as exc:
        return {"valid": False, "errors": [f"XML invalido: {exc}"], "warnings": []}
    errors = []
    warnings = []
    if root.tag != "mxfile":
        errors.append("Raiz mxfile ausente.")
    graph_root = root.find(".//root")
    if graph_root is None:
        errors.append("mxGraphModel/root ausente.")
        return {"valid": False, "errors": errors, "warnings": warnings}
    cells = graph_root.findall("mxCell")
    ids = {cell.get("id") for cell in cells}
    for edge in [cell for cell in cells if cell.get("edge") == "1"]:
        if edge.get("source") not in ids:
            errors.append(f"source inexistente: {edge.get('source')}")
        if edge.get("target") not in ids:
            errors.append(f"target inexistente: {edge.get('target')}")
    for vertex in [cell for cell in cells if cell.get("vertex") == "1"]:
        if not vertex.get("value") and not str(vertex.get("id", "")).startswith("group-"):
            warnings.append(f"no sem label: {vertex.get('id')}")
    warnings.extend(f"nos sobrepostos: {left} e {right}" for left, right in find_overlaps(cells))
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def find_overlaps(cells: list[ElementTree.Element]) -> list[tuple[str, str]]:
    vertices = [
        cell
        for cell in cells
        if cell.get("vertex") == "1"
        and cell.get("id") not in {"diagram-title", "diagram-legend"}
        and not str(cell.get("id", "")).startswith("group-")
    ]
    boxes = []
    for cell in vertices:
        geometry = cell.find("mxGeometry")
        if geometry is None:
            continue
        boxes.append(
            (
                cell.get("id") or "-",
                cell.get("parent") or "1",
                float(geometry.get("x") or 0),
                float(geometry.get("y") or 0),
                float(geometry.get("width") or 0),
                float(geometry.get("height") or 0),
            )
        )
    overlaps = []
    for index, left in enumerate(boxes):
        for right in boxes[index + 1 :]:
            if left[1] == right[1] and boxes_overlap(left, right):
                overlaps.append((left[0], right[0]))
    return overlaps


def boxes_overlap(left: tuple[str, str, float, float, float, float], right: tuple[str, str, float, float, float, float]) -> bool:
    _, _, lx, ly, lw, lh = left
    _, _, rx, ry, rw, rh = right
    return lw > 0 and lh > 0 and rw > 0 and rh > 0 and lx < rx + rw and lx + lw > rx and ly < ry + rh and ly + lh > ry


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_drawio.py <diagram.drawio>", file=sys.stderr)
        return 2
    result = validate(Path(sys.argv[1]))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
