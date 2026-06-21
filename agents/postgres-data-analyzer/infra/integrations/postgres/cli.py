#!/usr/bin/env python3
"""CLI for the Postgres repository."""

from __future__ import annotations

import argparse
import json
import sys

from postgres_repository import PostgresRepository, PostgresRepositoryError


def main() -> int:
    parser = argparse.ArgumentParser(description="Postgres integration CLI")
    parser.add_argument("--database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("test-connection")
    subparsers.add_parser("list-schemas")

    tables = subparsers.add_parser("list-tables")
    tables.add_argument("--schema")
    tables.add_argument("--limit", type=int, default=200)

    describe = subparsers.add_parser("describe-table")
    add_table_args(describe)

    query = subparsers.add_parser("run-readonly-query")
    query.add_argument("--query", required=True)
    query.add_argument("--limit", type=int, default=100)

    profile = subparsers.add_parser("profile-table")
    add_table_args(profile)
    profile.add_argument("--limit-columns", type=int, default=30)

    sensitive = subparsers.add_parser("detect-sensitive-columns")
    sensitive.add_argument("--schema")

    cpf = subparsers.add_parser("analyze-cpf-column")
    add_table_args(cpf)
    cpf.add_argument("--column", required=True)

    args = parser.parse_args()
    try:
        repo = PostgresRepository(database=args.database)
        result = run_command(repo, args)
    except (PostgresRepositoryError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def add_table_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--schema", required=True)
    parser.add_argument("--table", required=True)


def run_command(repo: PostgresRepository, args: argparse.Namespace) -> dict:
    if args.command == "test-connection":
        return repo.test_connection()
    if args.command == "list-schemas":
        return repo.list_schemas()
    if args.command == "list-tables":
        return repo.list_tables(schema=args.schema, limit=args.limit)
    if args.command == "describe-table":
        return repo.describe_table(schema=args.schema, table=args.table)
    if args.command == "run-readonly-query":
        return repo.run_readonly_query(query=args.query, limit=args.limit)
    if args.command == "profile-table":
        return repo.profile_table(schema=args.schema, table=args.table, limit_columns=args.limit_columns)
    if args.command == "detect-sensitive-columns":
        return repo.detect_sensitive_columns(schema=args.schema)
    if args.command == "analyze-cpf-column":
        return repo.analyze_cpf_column(schema=args.schema, table=args.table, column=args.column)
    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
