#!/usr/bin/env python3
"""Runner for detect-error-patterns."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    event_message,
    extract_endpoint,
    extract_status_code,
    get_events,
    group_by_message,
    is_error_event,
    load_events_payload,
    normalize_message,
    print_error,
    render_counter,
    summarize,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run aws-cloudwatch-log-analyzer/detect-error-patterns")
    parser.add_argument("--region")
    parser.add_argument("--log-group")
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--filter-pattern")
    parser.add_argument("--group-by", choices=["message", "status_code", "endpoint", "stream"], default="message")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        payload = load_events_payload(args)
        write_output(render(payload, args), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(payload: dict, args: argparse.Namespace) -> str:
    events = [event for event in get_events(payload) if is_error_event(event)]
    counter, examples = group_events(events, args.group_by)
    lines = [
        "# Error Patterns",
        "",
        "## Consulta",
        "",
        f"- Group by: {args.group_by}",
        f"- Eventos de erro: {len(events)}",
        "",
        "## Padroes",
        "",
        *render_counter(counter),
        "",
        "## Exemplos",
        "",
    ]
    for key, example in list(examples.items())[:10]:
        lines.append(f"- {value_or_dash(key)}: {summarize(example.get('message'), 220)}")
    if not examples:
        lines.append("- Nenhum exemplo.")
    return "\n".join(lines).rstrip() + "\n"


def group_events(events: list[dict], group_by: str) -> tuple[Counter[str], dict[str, dict]]:
    if group_by == "message":
        counter = group_by_message(events)
        examples = {}
        for event in events:
            examples.setdefault(normalize_message(event_message(event)), event)
        return counter, examples
    counter: Counter[str] = Counter()
    examples: dict[str, dict] = {}
    for event in events:
        message = event_message(event)
        if group_by == "status_code":
            key = extract_status_code(message)
        elif group_by == "endpoint":
            key = extract_endpoint(message)
        else:
            key = value_or_dash(event.get("log_stream_name"))
        counter[key] += 1
        examples.setdefault(key, event)
    return counter, examples


if __name__ == "__main__":
    raise SystemExit(main())
