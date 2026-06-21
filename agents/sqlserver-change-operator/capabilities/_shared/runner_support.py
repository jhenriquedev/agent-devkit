#!/usr/bin/env python3
"""Shared helpers for SQL Server Change Operator runners."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
SQLSERVER_DIR = AGENT_DIR / "infra" / "integrations" / "sqlserver"

sys.path.insert(0, str(SQLSERVER_DIR))

from sqlserver_change_repository import (  # pylint: disable=import-error
    SqlServerChangeRepository,
    SqlServerChangeRepositoryError,
)


def run_capability(capability: str) -> int:
    parser = argparse.ArgumentParser(description=f"Run sqlserver-change-operator/{capability}")
    add_common_args(parser)
    args = parser.parse_args()
    try:
        preflight(capability, args)
        payload = load_fixture(args.fixture) if args.fixture else execute(capability, args)
        write_output(render(capability, payload, args), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--database")
    parser.add_argument("--path")
    parser.add_argument("--rollback-path")
    parser.add_argument("--name")
    parser.add_argument("--schema")
    parser.add_argument("--table")
    parser.add_argument("--key-column")
    parser.add_argument("--input")
    parser.add_argument("--set-json")
    parser.add_argument("--where", dest="where_sql")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-delete", action="store_true")
    parser.add_argument("--max-affected-rows", type=int)
    parser.add_argument("--fixture")
    parser.add_argument("--output")


def preflight(capability: str, args: argparse.Namespace) -> None:
    if capability == "delete-records" and args.execute and not args.confirm_delete:
        raise SqlServerChangeRepositoryError("--confirm-delete is required")


def execute(capability: str, args: argparse.Namespace) -> dict[str, Any]:
    repo = SqlServerChangeRepository(database=args.database)
    if capability == "test-write-permissions":
        return repo.test_write_permissions(execute=args.execute)
    if capability == "plan-migration":
        require(args.path, "--path")
        return repo.plan_migration(path=args.path)
    if capability == "apply-migration":
        require(args.path, "--path")
        return repo.apply_migration(path=args.path, rollback_path=args.rollback_path, name=args.name, execute=args.execute)
    if capability == "rollback-migration":
        require(args.path, "--path")
        return repo.rollback_migration(path=args.path, execute=args.execute)
    if capability == "run-write-script":
        require(args.path, "--path")
        return repo.run_write_script(path=args.path, execute=args.execute)
    if capability == "create-object":
        require(args.path, "--path")
        return repo.create_object(path=args.path, execute=args.execute)
    if capability == "update-records":
        require(args.schema, "--schema")
        require(args.table, "--table")
        require(args.set_json, "--set-json")
        require(args.where_sql, "--where")
        return repo.update_records(
            schema=args.schema,
            table=args.table,
            set_json=json.loads(args.set_json),
            where_sql=args.where_sql,
            execute=args.execute,
            max_affected_rows=args.max_affected_rows,
        )
    if capability == "delete-records":
        require(args.schema, "--schema")
        require(args.table, "--table")
        require(args.where_sql, "--where")
        return repo.delete_records(
            schema=args.schema,
            table=args.table,
            where_sql=args.where_sql,
            execute=args.execute,
            confirm_delete=args.confirm_delete,
            max_affected_rows=args.max_affected_rows,
        )
    if capability == "upsert-records":
        require(args.schema, "--schema")
        require(args.table, "--table")
        require(args.key_column, "--key-column")
        require(args.input, "--input")
        return repo.upsert_records(schema=args.schema, table=args.table, key_column=args.key_column, input_path=args.input, execute=args.execute)
    if capability == "backup-records":
        require(args.schema, "--schema")
        require(args.table, "--table")
        require(args.where_sql, "--where")
        return repo.backup_records(schema=args.schema, table=args.table, where_sql=args.where_sql, execute=args.execute)
    if capability == "change-report":
        return repo.change_report()
    raise ValueError(f"unsupported capability: {capability}")


def render(capability: str, payload: dict[str, Any], args: argparse.Namespace) -> str:
    title = TITLE_BY_CAPABILITY.get(capability, capability.replace("-", " ").title())
    lines = [f"# SQL Server {title}", "", database_line(payload, args.database)]
    if capability in {"plan-migration", "apply-migration", "rollback-migration", "run-write-script", "create-object"}:
        plan = payload.get("plan") or payload
        if payload.get("dry_run"):
            lines.extend(["", "Re-run with `--execute` after reviewing this plan."])
        lines.extend(["", *render_plan(plan)])
    elif capability in {"update-records", "delete-records"}:
        lines.extend(
            [
                f"- Dry-run: {yes_no(payload.get('dry_run'))}",
                f"- Where: {value_or_dash(payload.get('where_sql'))}",
                f"- Max affected rows: {value_or_dash(payload.get('max_affected_rows'))}",
            ]
        )
        if payload.get("dry_run"):
            lines.append("Re-run with `--execute` after reviewing affected rows.")
        lines.extend(["", *render_plan(payload.get("plan") or {})])
    elif capability == "upsert-records":
        lines.extend([f"- Dry-run: {yes_no(payload.get('dry_run'))}", f"- Record count: {value_or_dash(payload.get('record_count'))}", "", *render_plan(payload.get("plan") or {})])
    elif capability == "backup-records":
        lines.extend(render_key_values(payload))
    elif capability == "change-report":
        lines.extend(["", *render_change_table(payload.get("changes") or [])])
    else:
        lines.extend(render_key_values(payload))
    return "\n".join(lines).rstrip() + "\n"


def render_plan(plan: dict[str, Any]) -> list[str]:
    operations = plan.get("operations") or []
    lines = [
        "## Plan",
        "",
        f"- Path: {value_or_dash(plan.get('path'))}",
        f"- Checksum: {value_or_dash(plan.get('checksum'))}",
        f"- Statements: {value_or_dash(plan.get('statement_count'))}",
        f"- Blocked: {yes_no(plan.get('blocked'))}",
        f"- Destructive: {yes_no(plan.get('destructive'))}",
        f"- Transactional: {yes_no(plan.get('transactional'))}",
        f"- Risk: {value_or_dash(plan.get('risk_level'))}",
        f"- Rollback path: {value_or_dash(plan.get('rollback_path'))}",
        "",
        "## Operations",
        "",
    ]
    if not operations:
        lines.append("- No SQL statements detected.")
        return lines
    for index, operation in enumerate(operations, start=1):
        lines.append(f"{index}. {value_or_dash(operation.get('command'))}: {value_or_dash(operation.get('preview'))}")
    return lines


def render_key_values(payload: dict[str, Any]) -> list[str]:
    return [f"- {key}: {value_or_dash(value)}" for key, value in payload.items() if not isinstance(value, (list, dict))]


def render_change_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["| id | operation | name | status | affected_rows | executed_at |", "|---|---|---|---|---|---|"]
    if not rows:
        lines.append("| - | - | - | - | - | - |")
        return lines
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    value_or_dash(row.get("id")),
                    value_or_dash(row.get("operation_type")),
                    value_or_dash(row.get("name")),
                    value_or_dash(row.get("status")),
                    value_or_dash(row.get("affected_rows")),
                    value_or_dash(row.get("executed_at")),
                ]
            )
            + " |"
        )
    return lines


def load_fixture(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_output(markdown: str, output: str | None) -> None:
    if output:
        Path(output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)


def print_error(exc: Exception) -> int:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1


def require(value: Any, name: str) -> None:
    if not value:
        raise ValueError(f"{name} is required")


def database_line(payload: dict[str, Any], requested_database: str | None = None) -> str:
    return f"- Target database: {value_or_dash(payload.get('database') or requested_database)}"


def value_or_dash(value: Any) -> str:
    if value is None:
        return "-"
    text = " ".join(str(value).replace("\r", " ").replace("\n", " ").split())
    return text if text else "-"


def yes_no(value: Any) -> str:
    return "yes" if bool(value) else "no"


TITLE_BY_CAPABILITY = {
    "test-write-permissions": "Write Permissions",
    "plan-migration": "Migration Plan",
    "apply-migration": "Apply Migration",
    "rollback-migration": "Rollback Migration",
    "run-write-script": "Run Write Script",
    "create-object": "Create Object",
    "update-records": "Update Records",
    "delete-records": "Delete Records",
    "upsert-records": "Upsert Records",
    "backup-records": "Backup Records",
    "change-report": "Change Report",
}
