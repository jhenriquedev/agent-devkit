#!/usr/bin/env python3
"""Inspect a Draw.io .drawio file."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from xml.etree import ElementTree


def inspect(path: Path) -> dict:
    root = ElementTree.fromstring(path.read_text(encoding="utf-8"))
    cells = root.findall(".//mxCell")
    vertices = [cell for cell in cells if cell.get("vertex") == "1"]
    edges = [cell for cell in cells if cell.get("edge") == "1"]
    labels = [cell.get("value") for cell in vertices if cell.get("value")]
    return {
        "root": root.tag,
        "diagrams": len(root.findall("diagram")),
        "vertices": len(vertices),
        "edges": len(edges),
        "labels": labels[:20],
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: inspect_drawio.py <diagram.drawio>", file=sys.stderr)
        return 2
    print(json.dumps(inspect(Path(sys.argv[1])), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
