#!/usr/bin/env python3
"""Runner for upsert-records."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import database_line, get_repository, load_fixture, print_error, render_plan, value_or_dash, write_output, yes_no


def main() -> int:
    parser = argparse.ArgumentParser(description="Run database-change-operator/upsert-records")
    parser.add_argument("--schema", required=True)
    parser.add_argument("--table", required=True)
    parser.add_argument("--key-column", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-destructive", action="store_true")
    parser.add_argument("--max-affected-rows", type=int, default=1000)
    parser.add_argument("--database")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = (
            load_fixture(args.fixture)
            if args.fixture
            else get_repository(args.database).upsert_records(
                schema=args.schema,
                table=args.table,
                key_column=args.key_column,
                input_path=args.input,
                execute=args.execute,
                confirm_destructive=args.confirm_destructive,
                max_affected_rows=args.max_affected_rows,
            )
        )
        lines = [
            "# Upsert Records",
            "",
            database_line(payload, args.database),
            f"- Dry run: {yes_no(payload.get('dry_run'))}",
            f"- Status: {value_or_dash(payload.get('status'))}",
            f"- Record count: {value_or_dash(payload.get('record_count'))}",
            "",
        ]
        if payload.get("dry_run"):
            lines.extend(["## Execution", "", "- Re-run with `--execute` to upsert these records.", ""])
        if payload.get("plan"):
            lines.extend(render_plan(payload["plan"]))
        write_output("\n".join(lines).rstrip() + "\n", args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
