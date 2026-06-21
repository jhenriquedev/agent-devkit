#!/usr/bin/env python3
"""Runner for trace-request."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    event_message,
    get_events,
    is_error_event,
    load_events_payload,
    print_error,
    render_events_table,
    sort_events,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run aws-cloudwatch-log-analyzer/trace-request")
    parser.add_argument("--region")
    parser.add_argument("--log-group")
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--identifier", required=False)
    parser.add_argument("--identifier-type", default="identifier")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        if not args.identifier and not args.fixture:
            raise ValueError("--identifier is required when --fixture is not provided")
        payload = load_events_payload(args)
        write_output(render(payload, args), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(payload: dict, args: argparse.Namespace) -> str:
    identifier = args.identifier or payload.get("identifier")
    events = [
        event
        for event in get_events(payload)
        if not identifier or identifier in event_message(event)
    ]
    events = sort_events(events)
    error_count = sum(1 for event in events if is_error_event(event))
    lines = [
        "# Request Trace",
        "",
        "## Identificador",
        "",
        f"- Tipo: {value_or_dash(args.identifier_type or payload.get('identifier_type'))}",
        f"- Valor: {value_or_dash(identifier)}",
        f"- Eventos encontrados: {len(events)}",
        f"- Eventos com erro: {error_count}",
        "",
        "## Timeline",
        "",
        *render_events_table(events, limit=args.limit),
        "",
        "## Lacunas",
        "",
        "- Validar se outros log groups tambem participam do fluxo.",
    ]
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
