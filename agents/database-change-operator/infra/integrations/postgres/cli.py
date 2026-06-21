#!/usr/bin/env python3
"""CLI for the database change repository."""

from __future__ import annotations

import argparse
import json
import sys

from database_change_repository import DatabaseChangeRepository, DatabaseChangeRepositoryError


def main() -> int:
    parser = argparse.ArgumentParser(description="Database change integration CLI")
    parser.add_argument("--database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    perm = subparsers.add_parser("test-write-permissions")
    perm.add_argument("--execute", action="store_true")

    plan = subparsers.add_parser("plan-migration")
    plan.add_argument("--path", required=True)

    apply = subparsers.add_parser("apply-migration")
    apply.add_argument("--path", required=True)
    apply.add_argument("--name")
    apply.add_argument("--execute", action="store_true")

    rollback = subparsers.add_parser("rollback-migration")
    rollback.add_argument("--path", required=True)
    rollback.add_argument("--execute", action="store_true")

    script = subparsers.add_parser("run-write-script")
    script.add_argument("--path", required=True)
    script.add_argument("--execute", action="store_true")

    upsert = subparsers.add_parser("upsert-records")
    upsert.add_argument("--schema", required=True)
    upsert.add_argument("--table", required=True)
    upsert.add_argument("--key-column", required=True)
    upsert.add_argument("--input", required=True)
    upsert.add_argument("--execute", action="store_true")

    update = subparsers.add_parser("update-records")
    update.add_argument("--schema", required=True)
    update.add_argument("--table", required=True)
    update.add_argument("--set-json", required=True)
    update.add_argument("--where", required=True)
    update.add_argument("--execute", action="store_true")

    report = subparsers.add_parser("migration-report")

    args = parser.parse_args()
    try:
        repo = DatabaseChangeRepository(database=args.database)
        result = run_command(repo, args)
    except (DatabaseChangeRepositoryError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def run_command(repo: DatabaseChangeRepository, args: argparse.Namespace) -> dict:
    if args.command == "test-write-permissions":
        return repo.test_write_permissions(execute=args.execute)
    if args.command == "plan-migration":
        return repo.plan_migration(path=args.path)
    if args.command == "apply-migration":
        return repo.apply_migration(path=args.path, name=args.name, execute=args.execute)
    if args.command == "rollback-migration":
        return repo.rollback_migration(path=args.path, execute=args.execute)
    if args.command == "run-write-script":
        return repo.run_write_script(path=args.path, execute=args.execute)
    if args.command == "upsert-records":
        return repo.upsert_records(
            schema=args.schema,
            table=args.table,
            key_column=args.key_column,
            input_path=args.input,
            execute=args.execute,
        )
    if args.command == "update-records":
        return repo.update_records(
            schema=args.schema,
            table=args.table,
            set_json=json.loads(args.set_json),
            where_sql=args.where,
            execute=args.execute,
        )
    if args.command == "migration-report":
        return repo.migration_report()
    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
