#!/usr/bin/env python3
"""Runner for excel-workbook-builder/review-generated-workbook."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from workbook_support import inspect_workbook_deep  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Review a generated workbook")
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--required-sheet", action="append", default=[])
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        workbook = Path(args.workbook).expanduser().resolve()
        if not workbook.exists():
            raise ValueError(f"workbook not found: {workbook}")
        result = inspect_workbook_deep(workbook)
        sheet_names = {sheet["name"] for sheet in result["worksheets"]}
        missing_sheets = [sheet for sheet in args.required_sheet if sheet not in sheet_names]
        failures = []
        if result["worksheet_count"] == 0:
            failures.append("workbook has no worksheets")
        if result["formula_errors"]:
            failures.append("formula error markers found")
        failures.extend(f"required sheet missing: {sheet}" for sheet in missing_sheets)
        if args.strict and result.get("inspection_warnings"):
            failures.extend(result["inspection_warnings"])
        lines = [
            "# Workbook Review",
            "",
            f"- File: {result['file']}",
            f"- Package parts: {result['part_count']}",
            f"- Worksheets: {result['worksheet_count']}",
            f"- Formula count: {result['formula_count']}",
            f"- Data validations: {result['data_validation_count']}",
            f"- Formula errors: {', '.join(result['formula_errors']) if result['formula_errors'] else '-'}",
            f"- Required sheets missing: {', '.join(missing_sheets) if missing_sheets else '-'}",
            "",
            "## Quality Gate",
            "",
            "- Status: " + ("fail" if failures else "pass"),
        ]
        if failures:
            lines.extend(["", "## Failures", ""])
            lines.extend(f"- {failure}" for failure in failures)
        markdown = "\n".join(lines).rstrip() + "\n"
        if args.output:
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown, encoding="utf-8")
        else:
            print(markdown)
        return 1 if failures else 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
