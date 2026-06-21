#!/usr/bin/env python3
"""Runner for excel-workbook-builder/reconcile-datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from workbook_support import generate_workbook_from_dataset, load_tabular_file  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile two tabular datasets")
    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--compare-column", action="append", default=[])
    parser.add_argument("--tolerance", type=float, default=0.0)
    parser.add_argument("--output")
    parser.add_argument("--summary-output")
    args = parser.parse_args()

    try:
        left = load_tabular_file(Path(args.left).expanduser().resolve())
        right = load_tabular_file(Path(args.right).expanduser().resolve())
        result = reconcile(left, right, parse_csv_arg(args.key), args.compare_column, args.tolerance)
        output = (
            Path(args.output).expanduser().resolve()
            if args.output
            else Path.cwd() / "docs" / "generated" / "excel-workbook-builder" / "reconciliation.xlsx"
        )
        summary_output = (
            Path(args.summary_output).expanduser().resolve()
            if args.summary_output
            else output.with_suffix(".json")
        )
        summary_output.parent.mkdir(parents=True, exist_ok=True)
        summary_output.write_text(
            json.dumps(result["summary"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        generate_workbook_from_dataset(
            {
                "source": f"{left.get('source')} vs {right.get('source')}",
                "columns": result["columns"],
                "rows": result["rows"],
            },
            output,
            title="Relatorio de Conciliacao",
            summary=result["summary"],
        )
        print(f"Conciliacao gerada: {output}")
        print(f"Resumo: {summary_output}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def reconcile(
    left: dict[str, Any],
    right: dict[str, Any],
    keys: list[str],
    compare_columns: list[str],
    tolerance: float,
) -> dict[str, Any]:
    if not keys:
        raise ValueError("at least one key is required")
    compare_columns = expand_columns(compare_columns)
    left_index = {row_key(row, keys): row for row in left.get("rows", []) if has_key(row, keys)}
    right_index = {row_key(row, keys): row for row in right.get("rows", []) if has_key(row, keys)}
    item_keys = sorted(set(left_index) | set(right_index))
    rows = []
    summary = {
        "matched": 0,
        "different": 0,
        "left_only": 0,
        "right_only": 0,
        "keys": keys,
        "compare_columns": compare_columns,
    }
    for item_key in item_keys:
        left_row = left_index.get(item_key)
        right_row = right_index.get(item_key)
        differences: list[str] = []
        if left_row and right_row:
            status = "matched"
            for column in compare_columns:
                if not values_match(left_row.get(column), right_row.get(column), tolerance):
                    differences.append(column)
            if differences:
                status = "different"
            summary[status] += 1
        elif left_row:
            status = "left_only"
            summary[status] += 1
        else:
            status = "right_only"
            summary[status] += 1
        row = {"reconciliation_key": item_key, "status": status, "different_columns": ", ".join(differences)}
        for column in compare_columns:
            row[f"left_{column}"] = left_row.get(column) if left_row else None
            row[f"right_{column}"] = right_row.get(column) if right_row else None
            row[f"delta_{column}"] = value_delta(
                left_row.get(column) if left_row else None,
                right_row.get(column) if right_row else None,
            )
        rows.append(row)
    columns = ["reconciliation_key", "status", "different_columns"]
    for column in compare_columns:
        columns.extend([f"left_{column}", f"right_{column}", f"delta_{column}"])
    return {
        "columns": columns,
        "rows": rows,
        "summary": summary,
    }


def parse_csv_arg(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def expand_columns(values: list[str]) -> list[str]:
    columns: list[str] = []
    for value in values:
        for item in parse_csv_arg(value):
            if item not in columns:
                columns.append(item)
    return columns


def has_key(row: dict[str, Any], keys: list[str]) -> bool:
    return all(row.get(key) is not None for key in keys)


def row_key(row: dict[str, Any], keys: list[str]) -> str:
    return " | ".join(str(row.get(key)) for key in keys)


def values_match(left: Any, right: Any, tolerance: float) -> bool:
    if left == right:
        return True
    try:
        return abs(float(left) - float(right)) <= tolerance
    except (TypeError, ValueError):
        return str(left) == str(right)


def value_delta(left: Any, right: Any) -> float | None:
    try:
        return float(left) - float(right)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
