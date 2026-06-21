#!/usr/bin/env python3
"""Spreadsheet reconciliation helpers."""

from __future__ import annotations

import re
from collections import defaultdict
from decimal import Decimal
from typing import Any

from privacy import mask_row, mask_value
from profiling import to_decimal


def index_rows(rows: list[dict[str, str]], keys: list[str]) -> dict[tuple[str, ...], list[dict[str, str]]]:
    indexed: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        indexed[tuple(normalize_key_value(row.get(column, "")) for column in keys)].append(row)
    return indexed


def compare_rows(
    left: dict[str, str],
    right: dict[str, str],
    columns: list[str],
    numeric_tolerance: Decimal,
) -> list[dict[str, Any]]:
    differences = []
    for column in columns:
        left_value = left.get(column, "")
        right_value = right.get(column, "")
        left_number = to_decimal(left_value)
        right_number = to_decimal(right_value)
        if left_number is not None and right_number is not None:
            delta = abs(left_number - right_number)
            if delta <= numeric_tolerance:
                continue
            reason = "numeric_difference"
        elif normalize_key_value(left_value) == normalize_key_value(right_value):
            continue
        else:
            delta = None
            reason = "value_difference"
        differences.append(
            {
                "column": column,
                "left": mask_value(column, left_value),
                "right": mask_value(column, right_value),
                "reason": reason,
                "delta": str(delta) if delta is not None else None,
            }
        )
    return differences


def key_to_label(key: tuple[str, ...]) -> str:
    return "|".join(key)


def normalize_key_value(value: str) -> str:
    stripped = value.strip()
    digits = re.sub(r"\D", "", stripped)
    if len(digits) in {11, 14}:
        return digits
    return stripped.casefold()


__all__ = ["compare_rows", "index_rows", "key_to_label", "mask_row", "normalize_key_value"]
