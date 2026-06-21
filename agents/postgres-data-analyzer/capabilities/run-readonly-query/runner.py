#!/usr/bin/env python3
"""Runner for run-readonly-query."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import database_line, get_repository, load_fixture, print_error, render_table, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run postgres-data-analyzer/run-readonly-query")
    parser.add_argument("--query")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--database")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        if args.fixture:
            payload = load_fixture(args.fixture)
        else:
            if not args.query:
                raise ValueError("--query is required")
            payload = get_repository(args.database).run_readonly_query(query=args.query, limit=args.limit)
        rows = payload.get("rows") or []
        lines = ["# Postgres Readonly Query", "", database_line(payload, args.database), f"- Rows: {value_or_dash(payload.get('row_count', len(rows)))}", f"- Limit: {value_or_dash(payload.get('limit') or args.limit)}", "", *render_table(rows, limit=args.limit)]
        write_output("\n".join(lines).rstrip() + "\n", args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
