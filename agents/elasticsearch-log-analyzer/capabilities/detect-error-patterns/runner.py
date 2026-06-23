#!/usr/bin/env python3
"""Runner for detect-error-patterns."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import count_patterns, event_rows, fixture_events, get_repository, load_fixture, print_error, render_buckets, render_counter, search_kwargs, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run elasticsearch-log-analyzer/detect-error-patterns")
    add_args(parser)
    args = parser.parse_args()
    try:
        if args.fixture:
            payload = load_fixture(args.fixture)
            events = fixture_events(payload)
            timeline_buckets = payload.get("timeline_buckets") or []
        else:
            require_scope(args)
            if not args.level:
                args.level = "error"
            repo = get_repository()
            payload = repo.search_events(**search_kwargs(args))
            events = payload.get("events") or []
            timeline_result = repo.aggregate_timeline(
                source=args.source,
                start_time=args.start_time,
                end_time=args.end_time,
                service=args.service,
                environment=args.environment,
                level=args.level,
                query_text=args.query,
                time_field=args.time_field,
            )
            timeline_buckets = timeline_result.get("buckets") or []
        patterns = count_patterns(events)
        write_output(render(payload, events, patterns, timeline_buckets, args), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source")
    parser.add_argument("--from", dest="start_time")
    parser.add_argument("--to", dest="end_time")
    parser.add_argument("--service")
    parser.add_argument("--environment")
    parser.add_argument("--query")
    parser.add_argument("--level")
    parser.add_argument("--filters-json")
    parser.add_argument("--time-field")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--fixture")
    parser.add_argument("--output")


def require_scope(args: argparse.Namespace) -> None:
    if not args.source or not args.start_time or not args.end_time:
        raise ValueError("--source, --from, and --to are required when --fixture is not provided")


def render(payload: dict, events: list[dict], patterns: dict, timeline_buckets: list[dict], args: argparse.Namespace) -> str:
    lines = [
        "# Elasticsearch Error Patterns",
        "",
        f"- Source: {value_or_dash(payload.get('source') or args.source)}",
        f"- Events analyzed: {len(events)}",
        "",
        "## Timeline",
        "",
        *render_buckets(timeline_buckets, key_name="key_as_string"),
        "",
        "## Top Patterns",
        "",
        *render_counter(patterns),
        "",
        "## Samples",
        "",
        *event_rows(events, limit=10),
    ]
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
