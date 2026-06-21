#!/usr/bin/env python3
"""Runner for excel-workbook-builder/inspect-template."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from workbook_support import inspect_xlsx  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect an Excel workbook/template")
    parser.add_argument("--template")
    parser.add_argument("--workbook")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        source_arg = args.template or args.workbook
        if not source_arg:
            raise ValueError("--template or --workbook is required")
        source = Path(source_arg).expanduser().resolve()
        if not source.exists():
            raise ValueError(f"workbook not found: {source}")
        result = inspect_xlsx(source)
        lines = [
            "# Workbook Inspection",
            "",
            f"- File: {result['file']}",
            f"- Package parts: {result['part_count']}",
            f"- Worksheet count: {result['worksheet_count']}",
            f"- Formula errors: {', '.join(result['formula_errors']) if result['formula_errors'] else '-'}",
            "",
            "## Worksheets",
            "",
        ]
        for sheet in result["worksheets"]:
            lines.append(f"- {sheet['name']}: {sheet['rows']} row(s)")
        markdown = "\n".join(lines).rstrip() + "\n"
        if args.output:
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown, encoding="utf-8")
        else:
            print(markdown)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

