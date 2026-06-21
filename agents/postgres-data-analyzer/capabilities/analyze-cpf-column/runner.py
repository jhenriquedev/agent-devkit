#!/usr/bin/env python3
"""Runner for analyze-cpf-column."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import database_line, get_repository, load_fixture, print_error, render_key_values, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run postgres-data-analyzer/analyze-cpf-column")
    parser.add_argument("--schema")
    parser.add_argument("--table")
    parser.add_argument("--column")
    parser.add_argument("--database")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        if args.fixture:
            payload = load_fixture(args.fixture)
        else:
            if not args.schema or not args.table or not args.column:
                raise ValueError("--schema, --table, and --column are required")
            payload = get_repository(args.database).analyze_cpf_column(schema=args.schema, table=args.table, column=args.column)
        keys = ["total_rows", "blank_count", "invalid_format_count", "repeated_digits_count", "valid_count", "invalid_check_digit_count", "duplicated_document_count", "duplicated_row_count"]
        lines = ["# Postgres CPF Analysis", "", database_line(payload, args.database), f"- Target: {value_or_dash(payload.get('schema'))}.{value_or_dash(payload.get('table'))}.{value_or_dash(payload.get('column'))}", "", *render_key_values(payload, keys)]
        write_output("\n".join(lines).rstrip() + "\n", args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
