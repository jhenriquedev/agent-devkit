#!/usr/bin/env python3
"""Runner for excel-workbook-builder/validate-source-data."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from workbook_support import load_tabular_file  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate source data against a schema")
    parser.add_argument("--input", required=True)
    parser.add_argument("--schema", "--expected-schema", dest="schema", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        dataset = load_tabular_file(Path(args.input).expanduser().resolve())
        schema = json.loads(Path(args.schema).expanduser().resolve().read_text(encoding="utf-8"))
        report = validate(dataset, schema)
        markdown = render_report(report)
        if args.output:
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown, encoding="utf-8")
        else:
            print(markdown)
        return 0 if report["status"] == "pass" else 1
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def validate(dataset: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    columns = set(dataset.get("columns", []))
    rows = dataset.get("rows", [])
    errors = []
    warnings = []
    for column in schema.get("required_columns", []):
        if column not in columns:
            errors.append(f"Missing required column: {column}")
    for column, expected_type in (schema.get("types") or {}).items():
        if column not in columns:
            continue
        for index, row in enumerate(rows, start=2):
            value = row.get(column)
            if value is None:
                continue
            if expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Invalid type at row {index}, column {column}: expected number")
            if expected_type == "text" and not isinstance(value, str):
                errors.append(f"Invalid type at row {index}, column {column}: expected text")
    for column in schema.get("unique", []):
        if column not in columns:
            continue
        counts = Counter(row.get(column) for row in rows if row.get(column) is not None)
        duplicates = [str(value) for value, count in counts.items() if count > 1]
        if duplicates:
            errors.append(f"Duplicate values in {column}: {', '.join(duplicates)}")
    return {
        "status": "fail" if errors else "pass",
        "errors": errors,
        "warnings": warnings,
        "row_count": len(rows),
        "columns": sorted(columns),
    }


def render_report(report: dict[str, Any]) -> str:
    lines = [
        "# Source Data Validation",
        "",
        f"- Status: {report['status']}",
        f"- Rows: {report['row_count']}",
        f"- Columns: {', '.join(report['columns']) if report['columns'] else '-'}",
        "",
        "## Errors",
        "",
    ]
    lines.extend(f"- {item}" for item in report["errors"]) if report["errors"] else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in report["warnings"]) if report["warnings"] else lines.append("- None")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())

