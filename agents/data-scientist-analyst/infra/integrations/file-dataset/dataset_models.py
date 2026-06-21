#!/usr/bin/env python3
"""Shared models for local dataset analysis."""

from __future__ import annotations

from dataclasses import dataclass, field


class DataScientistError(RuntimeError):
    """Raised for user-facing dataset analysis errors."""


@dataclass(frozen=True)
class Dataset:
    source: str
    name: str
    format: str
    rows: list[dict[str, str]]
    columns: list[str]
    sha256: str
    original_row_count: int | None = None
    warnings: list[str] = field(default_factory=list)
