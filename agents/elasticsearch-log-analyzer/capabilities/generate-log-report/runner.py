#!/usr/bin/env python3
"""Runner for generate-log-report."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import count_patterns, event_rows, fixture_events, get_repository, load_fixture, print_error, render_counter, search_kwargs, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run elasticsearch-log-analyzer/generate-log-report")
    add_args(parser)
    args = parser.parse_args()
    try:
        if args.fixture:
            payload = load_fixture(args.fixture)
            events = fixture_events(payload)
            count = payload.get("count", len(events))
        else:
            require_scope(args)
            repo = get_repository()
            payload = repo.search_events(**search_kwargs(args))
            events = payload.get("events") or []
            count = repo.count_events(**search_kwargs(args)).get("count")
        write_output(render(payload, events, count, args), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def add_args(parser: argparse.ArgumentParser) -> None:
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


def render(payload: dict, events: list[dict], count: int, args: argparse.Namespace) -> str:
    lines = [
        "# Elasticsearch Log Report",
        "",
        "## Scope",
        "",
        f"- Source: {value_or_dash(payload.get('source') or args.source)}",
        f"- From: {value_or_dash(payload.get('start_time') or args.start_time)}",
        f"- To: {value_or_dash(payload.get('end_time') or args.end_time)}",
        f"- Service: {value_or_dash(args.service)}",
        f"- Environment: {value_or_dash(args.environment)}",
        f"- Query: {value_or_dash(args.query)}",
        "",
        "## Summary",
        "",
        f"- Matching events: {value_or_dash(count)}",
        f"- Loaded samples: {len(events)}",
        f"- Limit reached: {value_or_dash(len(events) >= args.limit if args.limit else False)}",
        "",
        "## Patterns",
        "",
        *render_counter(count_patterns(events)),
        "",
        "## Samples",
        "",
        *event_rows(events, limit=10),
        "",
        "## Next Steps",
        "",
        "- Validate the highest-frequency patterns against recent deploys or infrastructure events.",
        "- Narrow by service, environment, or trace ID if the result set is broad.",
    ]
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
