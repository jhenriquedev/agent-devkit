#!/usr/bin/env python3
"""Runner for run-write-script."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import database_line, get_repository, load_fixture, print_error, render_plan, value_or_dash, write_output, yes_no


def main() -> int:
    parser = argparse.ArgumentParser(description="Run database-change-operator/run-write-script")
    parser.add_argument("--path", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-destructive", action="store_true")
    parser.add_argument("--database")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = (
            load_fixture(args.fixture)
            if args.fixture
            else get_repository(args.database).run_write_script(
                path=args.path,
                execute=args.execute,
                confirm_destructive=args.confirm_destructive,
            )
        )
        lines = [
            "# Run Write Script",
            "",
            database_line(payload, args.database),
            f"- Dry run: {yes_no(payload.get('dry_run'))}",
            f"- Status: {value_or_dash(payload.get('status'))}",
            "",
        ]
        if payload.get("dry_run"):
            lines.extend(["## Execution", "", "- Re-run with `--execute` to run this script.", ""])
        if payload.get("plan"):
            lines.extend(render_plan(payload["plan"]))
        write_output("\n".join(lines).rstrip() + "\n", args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
