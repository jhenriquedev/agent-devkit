#!/usr/bin/env python3
"""Runner for detect-sensitive-columns."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import database_line, get_repository, load_fixture, print_error, render_table, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run postgres-data-analyzer/detect-sensitive-columns")
    parser.add_argument("--schema")
    parser.add_argument("--database")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = load_fixture(args.fixture) if args.fixture else get_repository(args.database).detect_sensitive_columns(schema=args.schema)
        columns = payload.get("columns") or []
        lines = ["# Postgres Sensitive Columns", "", database_line(payload, args.database), f"- Schema: {value_or_dash(payload.get('schema') or args.schema)}", f"- Findings: {len(columns)}", "", *render_table(columns, ["table_schema", "table_name", "column_name", "data_type", "sensitive_kind"])]
        write_output("\n".join(lines).rstrip() + "\n", args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
