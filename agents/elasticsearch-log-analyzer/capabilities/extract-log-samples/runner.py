#!/usr/bin/env python3
"""Runner for extract-log-samples."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import event_rows, fixture_events, get_repository, load_fixture, print_error, search_kwargs, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run elasticsearch-log-analyzer/extract-log-samples")
    add_args(parser)
    args = parser.parse_args()
    try:
        if args.fixture:
            payload = load_fixture(args.fixture)
            events = fixture_events(payload)
        else:
            require_scope(args)
            payload = get_repository().search_events(**search_kwargs(args))
            events = payload.get("events") or []
        write_output(render(payload, events, args), args.output)
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
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--fixture")
    parser.add_argument("--output")


def require_scope(args: argparse.Namespace) -> None:
    if not args.source or not args.start_time or not args.end_time:
        raise ValueError("--source, --from, and --to are required when --fixture is not provided")


def render(payload: dict, events: list[dict], args: argparse.Namespace) -> str:
    return "\n".join([
        "# Elasticsearch Log Samples",
        "",
        f"- Source: {value_or_dash(payload.get('source') or args.source)}",
        f"- Samples: {len(events[:args.limit])}",
        "",
        *event_rows(events, limit=args.limit),
    ]).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
