#!/usr/bin/env python3
"""Runner for test-write-permissions."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import database_line, get_repository, load_fixture, print_error, value_or_dash, write_output, yes_no, yes_no_or_dash


def main() -> int:
    parser = argparse.ArgumentParser(description="Run database-change-operator/test-write-permissions")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--database")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = load_fixture(args.fixture) if args.fixture else get_repository(args.database).test_write_permissions(execute=args.execute)
        checks = payload.get("checks") or []
        lines = [
            "# Database Write Permissions",
            "",
            database_line(payload, args.database),
            f"- Dry run: {yes_no(payload.get('dry_run'))}",
            f"- Write permissions: {yes_no_or_dash(payload.get('write_permissions'))}",
            f"- Rolled back: {yes_no_or_dash(payload.get('rolled_back'))}",
            f"- Message: {value_or_dash(payload.get('message'))}",
            "",
            "## Checks",
            "",
        ]
        lines.extend(f"- {value_or_dash(item)}" for item in checks)
        if not checks:
            lines.append("- create_temp_table")
            lines.append("- insert")
            lines.append("- update")
            lines.append("- delete")
        write_output("\n".join(lines).rstrip() + "\n", args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
