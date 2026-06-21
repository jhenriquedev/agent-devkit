#!/usr/bin/env python3
"""Runner for describe-table."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import database_line, get_repository, load_fixture, print_error, render_table, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run postgres-data-analyzer/describe-table")
    parser.add_argument("--schema")
    parser.add_argument("--table")
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
            payload = get_repository(args.database).describe_table(schema=args.schema, table=args.table)
        lines = [
            "# Postgres Table Description",
            "",
            database_line(payload, args.database),
            f"- Table: {value_or_dash(payload.get('schema'))}.{value_or_dash(payload.get('table'))}",
            "",
            "## Columns",
            "",
            *render_table(payload.get("columns") or [], ["column_name", "data_type", "is_nullable", "column_default"]),
            "",
            "## Indexes",
            "",
            *render_table(payload.get("indexes") or [], ["indexname", "indexdef"]),
            "",
            "## Constraints",
            "",
            *render_table(payload.get("constraints") or [], ["constraint_name", "constraint_type"]),
        ]
        write_output("\n".join(lines).rstrip() + "\n", args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
