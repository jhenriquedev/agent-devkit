#!/usr/bin/env python3
"""Runner for profile-table."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import database_line, get_repository, load_fixture, print_error, render_table, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run postgres-data-analyzer/profile-table")
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
        else:
            if not args.schema or not args.table:
                raise ValueError("--schema and --table are required")
            payload = get_repository(args.database).profile_table(schema=args.schema, table=args.table, limit_columns=args.limit_columns)
        columns = payload.get("columns") or []
        lines = ["# Postgres Table Profile", "", database_line(payload, args.database), f"- Table: {value_or_dash(payload.get('schema'))}.{value_or_dash(payload.get('table'))}", f"- Row count: {value_or_dash(payload.get('row_count'))}", "", *render_table(columns, ["column_name", "data_type", "total_rows", "null_count", "distinct_count"])]
        write_output("\n".join(lines).rstrip() + "\n", args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
