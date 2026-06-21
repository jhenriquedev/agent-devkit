#!/usr/bin/env python3
"""Runner for excel-workbook-builder/review-generated-workbook."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from workbook_support import inspect_xlsx  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Review a generated workbook")
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        workbook = Path(args.workbook).expanduser().resolve()
        if not workbook.exists():
            raise ValueError(f"workbook not found: {workbook}")
        result = inspect_xlsx(workbook)
        lines = [
            "# Workbook Review",
            "",
            f"- File: {result['file']}",
            f"- Package parts: {result['part_count']}",
            f"- Worksheets: {result['worksheet_count']}",
            f"- Formula errors: {', '.join(result['formula_errors']) if result['formula_errors'] else '-'}",
            "",
            "## Quality Gate",
            "",
            "- Status: " + ("fail" if result["formula_errors"] else "pass"),
        ]
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

