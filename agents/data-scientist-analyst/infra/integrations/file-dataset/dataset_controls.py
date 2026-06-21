#!/usr/bin/env python3
"""Read-size controls for local tabular datasets."""

from __future__ import annotations

from typing import Any


class DatasetControlError(RuntimeError):
    """Raised when dataset read controls are invalid."""


def positive_int_or_none(value: int | None, name: str) -> int | None:
    if value is None:
        return None
    if value <= 0:
        raise DatasetControlError(f"{name} must be greater than zero")
    return value


def apply_row_controls(
    rows: list[dict[str, str]],
    max_rows: int | None = None,
    sample_rows: int | None = None,
    original_row_count: int | None = None,
) -> tuple[list[dict[str, str]], list[str], int]:
    original_count = len(rows) if original_row_count is None else original_row_count
    controlled = rows
    warnings = []
    if max_rows is not None and len(controlled) > max_rows:
        controlled = controlled[:max_rows]
        warnings.append(f"dataset truncated to first {max_rows} rows from {original_count} original rows")
    if sample_rows is not None and len(controlled) > sample_rows:
        controlled = deterministic_sample(controlled, sample_rows)
        warnings.append(f"dataset sampled to {sample_rows} rows from {len(rows)} loaded rows")
    return controlled, warnings, original_count


def deterministic_sample(rows: list[dict[str, Any]], size: int) -> list[dict[str, Any]]:
    if size >= len(rows):
        return rows
    if size == 1:
        return [rows[0]]
    step = (len(rows) - 1) / (size - 1)
    indexes = sorted({round(index * step) for index in range(size)})
    return [rows[index] for index in indexes[:size]]
