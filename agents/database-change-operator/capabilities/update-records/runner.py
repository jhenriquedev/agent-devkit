#!/usr/bin/env python3
"""Runner for update-records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import database_line, get_repository, load_fixture, print_error, render_plan, value_or_dash, write_output, yes_no


def main() -> int:
    parser = argparse.ArgumentParser(description="Run database-change-operator/update-records")
    parser.add_argument("--schema", required=True)
    parser.add_argument("--table", required=True)
    parser.add_argument("--set-json", required=True)
    parser.add_argument("--where", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--database")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = (
            load_fixture(args.fixture)
            if args.fixture
            else get_repository(args.database).update_records(
                schema=args.schema,
                table=args.table,
                set_json=json.loads(args.set_json),
                where_sql=args.where,
                execute=args.execute,
            )
        )
        lines = [
            "# Update Records",
            "",
            database_line(payload, args.database),
            f"- Dry run: {yes_no(payload.get('dry_run'))}",
            f"- Status: {value_or_dash(payload.get('status'))}",
            f"- Affected rows before update: {value_or_dash(payload.get('affected_rows_before'))}",
            f"- Where: {value_or_dash(payload.get('where_sql'))}",
            "",
        ]
        if payload.get("dry_run"):
            lines.extend(["## Execution", "", "- Re-run with `--execute` to update these records.", ""])
        if payload.get("plan"):
            lines.extend(render_plan(payload["plan"]))
        write_output("\n".join(lines).rstrip() + "\n", args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
