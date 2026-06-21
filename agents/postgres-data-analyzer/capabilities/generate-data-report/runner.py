#!/usr/bin/env python3
"""Runner for generate-data-report."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import database_line, get_repository, load_fixture, print_error, render_table, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run postgres-data-analyzer/generate-data-report")
    parser.add_argument("--schema")
    parser.add_argument("--table")
    parser.add_argument("--limit-columns", type=int, default=30)
    parser.add_argument("--database")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        if args.fixture:
            payload = load_fixture(args.fixture)
            if args.database:
                payload.setdefault("database", args.database)
                if isinstance(payload.get("profile"), dict):
                    payload["profile"].setdefault("database", args.database)
        else:
            if not args.schema or not args.table:
                raise ValueError("--schema and --table are required")
            repo = get_repository(args.database)
            payload = {
                "profile": repo.profile_table(schema=args.schema, table=args.table, limit_columns=args.limit_columns),
                "sensitive": repo.detect_sensitive_columns(schema=args.schema),
            }
        write_output(render(payload), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(payload: dict) -> str:
    profile = payload.get("profile") or payload
    sensitive = payload.get("sensitive") or {}
    sensitive_columns = [
        item for item in (sensitive.get("columns") or [])
        if item.get("table_schema") == profile.get("schema") and item.get("table_name") == profile.get("table")
    ]
    columns = profile.get("columns") or []
    null_heavy = [item for item in columns if int(item.get("total_rows") or 0) and int(item.get("null_count") or 0) > int(item.get("total_rows") or 0) * 0.5]
    lines = [
        "# Postgres Data Report",
        "",
        "## Scope",
        "",
        f"- Table: {value_or_dash(profile.get('schema'))}.{value_or_dash(profile.get('table'))}",
        database_line(profile if profile.get("database") else payload, None),
        f"- Row count: {value_or_dash(profile.get('row_count'))}",
        f"- Columns profiled: {len(columns)}",
        "",
        "## Sensitive Columns",
        "",
        *render_table(sensitive_columns, ["column_name", "data_type", "sensitive_kind"]),
        "",
        "## High Null Columns",
        "",
        *render_table(null_heavy, ["column_name", "data_type", "total_rows", "null_count"]),
        "",
        "## Column Profile",
        "",
        *render_table(columns, ["column_name", "data_type", "total_rows", "null_count", "distinct_count"]),
        "",
        "## Recommendations",
        "",
        "- Review sensitive columns before sharing query outputs.",
        "- Investigate high-null columns before using them in reports.",
    ]
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
