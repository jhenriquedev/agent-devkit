#!/usr/bin/env python3
"""Shared helpers for Postgres Data Analyzer runners."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
POSTGRES_DIR = AGENT_DIR / "infra" / "integrations" / "postgres"


def load_fixture(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_repository(database: str | None = None) -> Any:
    sys.path.insert(0, str(POSTGRES_DIR))
    from postgres_repository import PostgresRepository  # pylint: disable=import-error

    return PostgresRepository(database=database)


def write_output(markdown: str, output: str | None) -> None:
    if output:
        Path(output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)


def print_error(exc: Exception) -> int:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1


def value_or_dash(value: Any) -> str:
    if value is None:
        return "-"
    text = " ".join(str(value).replace("\r", " ").replace("\n", " ").split())
    return text if text else "-"


def database_line(payload: dict[str, Any], requested_database: str | None = None) -> str:
    return f"- Database: {value_or_dash(payload.get('database') or requested_database)}"


def render_table(rows: list[dict[str, Any]], columns: list[str] | None = None, limit: int = 20) -> list[str]:
    if not rows:
        return ["| - |", "|---|", "| No rows. |"]
    selected = columns or list(rows[0].keys())
    lines = ["| " + " | ".join(selected) + " |", "|" + "|".join("---" for _ in selected) + "|"]
    for row in rows[:limit]:
        lines.append("| " + " | ".join(mask_if_sensitive(key, row.get(key)) for key in selected) + " |")
    return lines


def mask_if_sensitive(column: str, value: Any) -> str:
    text = value_or_dash(value)
    lowered = column.lower()
    if "cpf" in lowered or "document" in lowered:
        return mask_cpf(text)
    return text


def mask_cpf(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 11:
        return value
    return f"{digits[:3]}.***.***-{digits[-2:]}"


def render_key_values(payload: dict[str, Any], keys: list[str]) -> list[str]:
    return [f"- {key}: {value_or_dash(payload.get(key))}" for key in keys]
