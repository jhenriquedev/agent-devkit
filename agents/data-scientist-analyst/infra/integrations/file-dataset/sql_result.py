#!/usr/bin/env python3
"""Normalize delegated SQL analyzer results into tabular datasets."""

from __future__ import annotations

from typing import Any


def normalize_sql_result(result: dict[str, Any]) -> dict[str, Any]:
    rows = extract_sql_rows(result)
    if rows is None:
        return {
            "kind": "raw_output",
            "raw_output": result.get("raw_output", result),
            "warnings": ["database result is not tabular JSON; downstream dataset analysis is unavailable"],
        }
    columns = extract_sql_columns(result, rows)
    normalized_rows = [
        {column: value_to_string(row.get(column, "")) for column in columns}
        for row in rows
    ]
    return {
        "kind": "tabular_dataset",
        "source": {
            "table": result.get("table"),
            "database": result.get("database"),
            "schema": result.get("schema"),
        },
        "dataset": {
            "row_count": len(normalized_rows),
            "column_count": len(columns),
            "truncated": bool(result.get("truncated", False)),
            "warnings": result.get("warnings", []),
        },
        "columns": columns,
        "rows": normalized_rows,
    }


def extract_sql_rows(result: dict[str, Any]) -> list[dict[str, Any]] | None:
    candidate = result.get("rows")
    if candidate is None and isinstance(result.get("result"), dict):
        candidate = result["result"].get("rows")
    if candidate is None and isinstance(result.get("data"), list):
        candidate = result.get("data")
    if not isinstance(candidate, list) or not all(isinstance(row, dict) for row in candidate):
        return None
    return candidate


def extract_sql_columns(result: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    candidate = result.get("columns")
    if candidate is None and isinstance(result.get("result"), dict):
        candidate = result["result"].get("columns")
    if isinstance(candidate, list) and all(isinstance(column, str) for column in candidate):
        columns = list(candidate)
    else:
        columns = []
    for row in rows:
        for column in row:
            if column not in columns:
                columns.append(str(column))
    return columns


def value_to_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value)
