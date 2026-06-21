#!/usr/bin/env python3
"""CLI for the TOPdesk repository."""

from __future__ import annotations

import argparse
import json
import sys

from topdesk_repository import TopdeskRepository, TopdeskRepositoryError


def main() -> int:
    parser = argparse.ArgumentParser(description="TOPdesk integration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-incidents")
    list_parser.add_argument("--query")
    list_parser.add_argument("--status")
    list_parser.add_argument("--operator-group")
    list_parser.add_argument("--limit", type=int, default=50)

    get_parser = subparsers.add_parser("get-incident")
    get_parser.add_argument("--id")
    get_parser.add_argument("--number")

    trail_parser = subparsers.add_parser("get-progress-trail")
    trail_parser.add_argument("--id")
    trail_parser.add_argument("--number")

    create_parser = subparsers.add_parser("create-incident")
    create_parser.add_argument("--fields-json", required=True)
    create_parser.add_argument("--execute", action="store_true")

    update_parser = subparsers.add_parser("update-incident")
    update_parser.add_argument("--id")
    update_parser.add_argument("--number")
    update_parser.add_argument("--fields-json", required=True)
    update_parser.add_argument("--execute", action="store_true")

    catalog_parser = subparsers.add_parser("get-catalog")
    catalog_parser.add_argument("--catalog", required=True)

    persons_parser = subparsers.add_parser("search-persons")
    persons_parser.add_argument("--query")
    persons_parser.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()
    try:
        repo = TopdeskRepository()
        result = run_command(repo, args)
    except (TopdeskRepositoryError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def run_command(repo: TopdeskRepository, args: argparse.Namespace) -> dict:
    if args.command == "list-incidents":
        return repo.list_incidents(
            query=args.query,
            status=args.status,
            operator_group=args.operator_group,
            limit=args.limit,
        )
    if args.command == "get-incident":
        return repo.get_incident(incident_id=args.id, number=args.number)
    if args.command == "get-progress-trail":
        return repo.get_progress_trail(incident_id=args.id, number=args.number)
    if args.command == "create-incident":
        return repo.create_incident(json.loads(args.fields_json), dry_run=not args.execute)
    if args.command == "update-incident":
        return repo.update_incident(
            json.loads(args.fields_json),
            incident_id=args.id,
            number=args.number,
            dry_run=not args.execute,
        )
    if args.command == "get-catalog":
        return repo.get_catalog(args.catalog)
    if args.command == "search-persons":
        return repo.search_persons(args.query, limit=args.limit)
    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
