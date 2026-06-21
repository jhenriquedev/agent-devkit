#!/usr/bin/env python3
"""Runner for trace-request."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import event_rows, fixture_events, get_repository, load_fixture, print_error, search_kwargs, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run elasticsearch-log-analyzer/trace-request")
    parser.add_argument("--source")
    parser.add_argument("--request-id")
    parser.add_argument("--from", dest="start_time")
    parser.add_argument("--to", dest="end_time")
    parser.add_argument("--service")
    parser.add_argument("--environment")
    parser.add_argument("--time-field")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        if args.fixture:
            payload = load_fixture(args.fixture)
            events = fixture_events(payload)
        else:
            if not args.source or not args.request_id or not args.start_time or not args.end_time:
                raise ValueError("--source, --request-id, --from, and --to are required when --fixture is not provided")
            args.query = build_request_query(args.request_id)
            args.level = None
            args.filters_json = None
            payload = get_repository().search_events(**search_kwargs(args))
            events = sorted(payload.get("events") or [], key=lambda item: value_or_dash(item.get("timestamp")))
        write_output(render(payload, events, args), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def build_request_query(request_id: str) -> str:
    escaped = request_id.replace('"', '\\"')
    return f'"{escaped}" OR trace.id:"{escaped}" OR trace_id:"{escaped}" OR correlation_id:"{escaped}" OR request_id:"{escaped}"'


def render(payload: dict, events: list[dict], args: argparse.Namespace) -> str:
    lines = [
        "# Elasticsearch Request Trace",
        "",
        f"- Source: {value_or_dash(payload.get('source') or args.source)}",
        f"- Request ID: {value_or_dash(args.request_id or payload.get('request_id'))}",
        f"- Events: {len(events)}",
        "",
        "## Timeline",
        "",
        *event_rows(events, limit=args.limit),
    ]
    if not events:
        lines.extend(["", "## Recommendation", "", "- No event found. Consider widening the time window or source pattern."])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
