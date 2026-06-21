#!/usr/bin/env python3
"""Runner for correlate-azure-card-logs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import event_rows, fixture_events, get_repository, load_fixture, print_error, search_kwargs, truncate, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run elasticsearch-log-analyzer/correlate-azure-card-logs")
    parser.add_argument("--source")
    parser.add_argument("--from", dest="start_time")
    parser.add_argument("--to", dest="end_time")
    parser.add_argument("--query")
    parser.add_argument("--service")
    parser.add_argument("--environment")
    parser.add_argument("--time-field")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--card-fixture")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        card = load_fixture(args.card_fixture).get("work_item") if args.card_fixture else {}
        if args.fixture:
            payload = load_fixture(args.fixture)
            events = fixture_events(payload)
        else:
            if not args.source or not args.start_time or not args.end_time:
                raise ValueError("--source, --from, and --to are required when --fixture is not provided")
            args.query = args.query or query_from_card(card)
            args.level = None
            args.filters_json = None
            payload = get_repository().search_events(**search_kwargs(args))
            events = payload.get("events") or []
        write_output(render(payload, events, card, args), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def query_from_card(card: dict) -> str | None:
    title = value_or_dash(card.get("title"))
    tags = " ".join(card.get("tags") or [])
    text = " ".join(item for item in [title, tags] if item and item != "-")
    return truncate(text, 180) if text else None


def render(payload: dict, events: list[dict], card: dict, args: argparse.Namespace) -> str:
    lines = [
        "# Azure Card Log Correlation",
        "",
        "## Card Context",
        "",
        f"- Card: {value_or_dash(card.get('id'))}",
        f"- Title: {value_or_dash(card.get('title'))}",
        f"- Query: {value_or_dash(args.query or query_from_card(card))}",
        "",
        "## Log Evidence",
        "",
        f"- Source: {value_or_dash(payload.get('source') or args.source)}",
        f"- Events: {len(events)}",
        "",
        *event_rows(events, limit=10),
        "",
        "## Correlation",
        "",
        f"- Confidence: {'medium' if events else 'low'}",
        "- Confidence is based on textual/log matching only.",
    ]
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
