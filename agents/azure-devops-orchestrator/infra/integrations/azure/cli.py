#!/usr/bin/env python3
"""CLI for the Azure DevOps repository."""

from __future__ import annotations

import argparse
import json
import sys

from azure_repository import AzureRepository, AzureRepositoryError


def main() -> int:
    parser = argparse.ArgumentParser(description="Azure DevOps Orchestrator integration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-work-items")
    list_parser.add_argument("--project")
    list_parser.add_argument("--wiql")
    list_parser.add_argument("--state")
    list_parser.add_argument("--assigned-to")
    list_parser.add_argument("--tag", action="append", default=[])
    list_parser.add_argument("--limit", type=int, default=50)

    get_parser = subparsers.add_parser("get-work-item")
    get_parser.add_argument("--project")
    get_parser.add_argument("--id", required=True, type=int)
    get_parser.add_argument("--field", action="append", default=[])
    get_parser.add_argument("--expand-relations", action="store_true")

    comments_parser = subparsers.add_parser("get-work-item-comments")
    comments_parser.add_argument("--project")
    comments_parser.add_argument("--id", required=True, type=int)
    comments_parser.add_argument("--limit", type=int, default=50)
    comments_parser.add_argument("--order", choices=["asc", "desc"], default="asc")

    add_comment_parser = subparsers.add_parser("add-comment")
    add_comment_parser.add_argument("--project")
    add_comment_parser.add_argument("--id", required=True, type=int)
    add_comment_parser.add_argument("--comment", required=True)
    add_comment_parser.add_argument("--execute", action="store_true")

    update_parser = subparsers.add_parser("update-work-item")
    update_parser.add_argument("--project")
    update_parser.add_argument("--id", required=True, type=int)
    update_parser.add_argument("--operations-json", required=True)
    update_parser.add_argument("--reason")
    update_parser.add_argument("--execute", action="store_true")

    users_parser = subparsers.add_parser("find-users")
    users_parser.add_argument("--project")
    users_parser.add_argument("--query", required=True)
    users_parser.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    try:
        repo = AzureRepository()
        result = run_command(repo, args)
    except (AzureRepositoryError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def run_command(repo: AzureRepository, args: argparse.Namespace) -> dict:
    if args.command == "list-work-items":
        return repo.list_work_items(
            project=args.project,
            wiql=args.wiql,
            state=args.state,
            assigned_to=args.assigned_to,
            tags=args.tag,
            limit=args.limit,
        )
    if args.command == "get-work-item":
        return repo.get_work_item(
            args.id,
            project=args.project,
            fields=args.field or None,
            expand_relations=args.expand_relations,
        )
    if args.command == "get-work-item-comments":
        return repo.get_work_item_comments(
            args.id,
            project=args.project,
            limit=args.limit,
            order=args.order,
        )
    if args.command == "add-comment":
        return repo.add_comment(
            args.id,
            args.comment,
            project=args.project,
            dry_run=not args.execute,
        )
    if args.command == "update-work-item":
        operations = json.loads(args.operations_json)
        if not isinstance(operations, list):
            raise ValueError("--operations-json must decode to a JSON array")
        return repo.update_work_item(
            args.id,
            operations,
            project=args.project,
            dry_run=not args.execute,
            reason=args.reason,
        )
    if args.command == "find-users":
        return repo.find_users(args.query, project=args.project, limit=args.limit)
    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
