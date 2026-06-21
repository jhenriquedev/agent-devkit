#!/usr/bin/env python3
"""Runner for search-log-events."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import event_rows, get_repository, load_fixture, print_error, search_kwargs, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run elasticsearch-log-analyzer/search-log-events")
    add_search_args(parser)
    args = parser.parse_args()
    try:
        if args.fixture:
            payload = load_fixture(args.fixture)
        else:
            require_scope(args)
            repo = get_repository()
            payload = repo.search_events(**search_kwargs(args))
            payload["count"] = repo.count_events(**search_kwargs(args)).get("count")
        write_output(render(payload, args), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def add_search_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source")
    parser.add_argument("--from", dest="start_time")
    parser.add_argument("--to", dest="end_time")
    parser.add_argument("--query")
    parser.add_argument("--service")
    parser.add_argument("--environment")
    parser.add_argument("--level")
    parser.add_argument("--filters-json")
    parser.add_argument("--time-field")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--fixture")
    parser.add_argument("--output")


def require_scope(args: argparse.Namespace) -> None:
    if not args.source or not args.start_time or not args.end_time:
        raise ValueError("--source, --from, and --to are required when --fixture is not provided")


def render(payload: dict, args: argparse.Namespace) -> str:
    events = payload.get("events") or []
    lines = [
        "# Elasticsearch Log Events",
        "",
        "## Scope",
        "",
        f"- Source: {value_or_dash(payload.get('source') or args.source)}",
        f"- From: {value_or_dash(payload.get('start_time') or args.start_time)}",
        f"- To: {value_or_dash(payload.get('end_time') or args.end_time)}",
        f"- Service: {value_or_dash(args.service)}",
        f"- Environment: {value_or_dash(args.environment)}",
        f"- Level: {value_or_dash(args.level)}",
        f"- Query: {value_or_dash(args.query)}",
        f"- Total: {value_or_dash(payload.get('count', payload.get('total')))}",
        "",
        "## Events",
        "",
        *event_rows(events),
    ]
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
