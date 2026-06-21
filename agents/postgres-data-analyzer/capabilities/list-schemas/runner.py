#!/usr/bin/env python3
"""Runner for list-schemas."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import database_line, get_repository, load_fixture, print_error, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run postgres-data-analyzer/list-schemas")
    parser.add_argument("--database")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = load_fixture(args.fixture) if args.fixture else get_repository(args.database).list_schemas()
        schemas = payload.get("schemas") or []
        lines = ["# Postgres Schemas", "", database_line(payload, args.database), f"- Count: {len(schemas)}", "", "## Schemas", ""]
        lines.extend(f"- {value_or_dash(item.get('schema_name'))}" for item in schemas)
        if not schemas:
            lines.append("- None.")
        write_output("\n".join(lines).rstrip() + "\n", args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
