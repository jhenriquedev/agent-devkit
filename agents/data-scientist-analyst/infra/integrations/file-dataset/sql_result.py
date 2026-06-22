#!/usr/bin/env python3
"""Normalize delegated SQL analyzer results into tabular datasets."""

from __future__ import annotations

import json
from pathlib import Path
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


def write_tabular_artifact(normalized: dict[str, Any], output: str | None) -> dict[str, Any] | None:
    if not output:
        return None
    if normalized.get("kind") != "tabular_dataset":
        return {
            "format": None,
            "output": None,
            "written": False,
            "warnings": ["only tabular_dataset results can be written as reusable dataset artifacts"],
        }
    path = Path(output).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "kind": "tabular_dataset",
        "source": normalized.get("source", {}),
        "columns": normalized.get("columns", []),
        "rows": normalized.get("rows", []),
        "dataset": normalized.get("dataset", {}),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "format": "json",
        "output": str(path),
        "written": True,
        "row_count": len(payload["rows"]),
        "column_count": len(payload["columns"]),
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
