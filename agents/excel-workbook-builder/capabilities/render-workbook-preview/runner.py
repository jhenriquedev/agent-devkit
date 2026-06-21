#!/usr/bin/env python3
"""Runner for excel-workbook-builder/render-workbook-preview."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from workbook_support import render_workbook_preview  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Render workbook preview")
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--sheet")
    parser.add_argument("--range")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        workbook = Path(args.workbook).expanduser().resolve()
        if not workbook.exists():
            raise ValueError(f"workbook not found: {workbook}")
        output = (
            Path(args.output).expanduser().resolve()
            if args.output
            else workbook.with_suffix(".png")
        )
        render_workbook_preview(workbook, output, sheet=args.sheet, cell_range=args.range)
        print(f"Preview gerado: {output}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

