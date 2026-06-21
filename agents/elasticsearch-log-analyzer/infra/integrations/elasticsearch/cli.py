#!/usr/bin/env python3
"""CLI for the Elasticsearch repository."""

from __future__ import annotations

import argparse
import json
import sys

from elasticsearch_repository import ElasticsearchRepository, ElasticsearchRepositoryError


def main() -> int:
    parser = argparse.ArgumentParser(description="Elasticsearch integration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-sources")
    list_parser.add_argument("--pattern")
    list_parser.add_argument("--limit", type=int, default=100)

    describe_parser = subparsers.add_parser("describe-source")
    describe_parser.add_argument("--source", required=True)

    search_parser = add_search_args(subparsers.add_parser("search-events"))

    count_parser = add_search_args(subparsers.add_parser("count-events"))

    terms_parser = add_search_args(subparsers.add_parser("aggregate-terms"))
    terms_parser.add_argument("--field", required=True)
    terms_parser.add_argument("--size", type=int, default=10)

    timeline_parser = add_search_args(subparsers.add_parser("aggregate-timeline"))
    timeline_parser.add_argument("--interval", default="5m")

    get_parser = subparsers.add_parser("get-event")
    get_parser.add_argument("--source", required=True)
    get_parser.add_argument("--event-id", required=True)

    args = parser.parse_args()
    try:
        repo = ElasticsearchRepository()
        result = run_command(repo, args)
    except (ElasticsearchRepositoryError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def add_search_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("--source", required=True)
    parser.add_argument("--from", dest="start_time", required=True)
    parser.add_argument("--to", dest="end_time", required=True)
    parser.add_argument("--query")
    parser.add_argument("--service")
    parser.add_argument("--environment")
    parser.add_argument("--level")
    parser.add_argument("--time-field")
    parser.add_argument("--limit", type=int, default=100)
    return parser


def run_command(repo: ElasticsearchRepository, args: argparse.Namespace) -> dict:
    if args.command == "list-sources":
        return repo.list_sources(pattern=args.pattern, limit=args.limit)
    if args.command == "describe-source":
        return repo.describe_source(source=args.source)
    if args.command == "search-events":
        return repo.search_events(**search_kwargs(args))
    if args.command == "count-events":
        return repo.count_events(**search_kwargs(args))
    if args.command == "aggregate-terms":
        return repo.aggregate_terms(**search_kwargs(args), field=args.field, size=args.size)
    if args.command == "aggregate-timeline":
        return repo.aggregate_timeline(**search_kwargs(args), interval=args.interval)
    if args.command == "get-event":
        return repo.get_event(source=args.source, event_id=args.event_id)
    raise ValueError(f"unsupported command: {args.command}")


def search_kwargs(args: argparse.Namespace) -> dict:
    return {
        "source": args.source,
        "start_time": args.start_time,
        "end_time": args.end_time,
        "query_text": args.query,
        "service": args.service,
        "environment": args.environment,
        "level": args.level,
        "time_field": args.time_field,
        "limit": args.limit,
    }


if __name__ == "__main__":
    raise SystemExit(main())
