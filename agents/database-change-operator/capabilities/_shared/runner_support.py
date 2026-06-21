#!/usr/bin/env python3
"""Shared helpers for Database Change Operator runners."""

from __future__ import annotations

import json
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
    from database_change_repository import DatabaseChangeRepository  # pylint: disable=import-error

    return DatabaseChangeRepository(database=database)


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
    return f"- Target database: {value_or_dash(payload.get('database') or requested_database)}"


def yes_no(value: Any) -> str:
    return "yes" if bool(value) else "no"


def yes_no_or_dash(value: Any) -> str:
    if value is None:
        return "-"
    return yes_no(value)


def render_key_values(payload: dict[str, Any], keys: list[str]) -> list[str]:
    return [f"- {key}: {value_or_dash(payload.get(key))}" for key in keys]


def render_plan(plan: dict[str, Any]) -> list[str]:
    operations = plan.get("operations") or []
    lines = [
        "## Plan",
        "",
        f"- Path: {value_or_dash(plan.get('path'))}",
        f"- Target database: {value_or_dash(plan.get('database'))}",
        f"- Checksum: {value_or_dash(plan.get('checksum'))}",
        f"- Statements: {value_or_dash(plan.get('statement_count'))}",
        f"- Blocked: {yes_no(plan.get('blocked'))}",
        f"- Destructive: {yes_no(plan.get('destructive'))}",
        f"- Transactional: {yes_no(plan.get('transactional'))}",
        f"- Rollback path: {value_or_dash(plan.get('rollback_path'))}",
        "",
        "## Operations",
        "",
    ]
    if not operations:
        lines.append("- No SQL statements detected.")
        return lines
    for index, operation in enumerate(operations, start=1):
        lines.append(
            f"{index}. {value_or_dash(operation.get('command'))}: "
            f"{value_or_dash(operation.get('preview'))}"
        )
    return lines


def render_migration_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| id | name | status | applied_at | rollback |",
        "|---|---|---|---|---|",
    ]
    if not rows:
        lines.append("| - | - | - | - | - |")
        return lines
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    value_or_dash(row.get("id")),
                    value_or_dash(row.get("name")),
                    value_or_dash(row.get("status")),
                    value_or_dash(row.get("applied_at")),
                    yes_no(row.get("rollback_available")),
                ]
            )
            + " |"
        )
    return lines
