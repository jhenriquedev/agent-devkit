#!/usr/bin/env python3
"""Runner for extract-log-samples."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    get_events,
    group_by_message,
    load_events_payload,
    print_error,
    render_events_table,
    sort_events,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run aws-cloudwatch-log-analyzer/extract-log-samples")
    parser.add_argument("--region")
    parser.add_argument("--log-group")
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--filter-pattern")
    parser.add_argument("--sample-size", type=int, default=5)
    parser.add_argument("--strategy", choices=["first", "last", "spread", "per-pattern"], default="first")
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
    events = sort_events(get_events(payload))
    samples = select_samples(events, args.strategy, args.sample_size)
    lines = [
        "# Log Samples",
        "",
        "## Estrategia",
        "",
        f"- Tipo: {args.strategy}",
        f"- Tamanho solicitado: {args.sample_size}",
        f"- Eventos disponiveis: {len(events)}",
        f"- Amostras retornadas: {len(samples)}",
        "",
        "## Amostras",
        "",
        *render_events_table(samples, limit=args.sample_size),
    ]
    return "\n".join(lines).rstrip() + "\n"


def select_samples(events: list[dict], strategy: str, sample_size: int) -> list[dict]:
    if sample_size <= 0:
        return []
    if strategy == "last":
        return events[-sample_size:]
    if strategy == "spread":
        if len(events) <= sample_size:
            return events
        step = max(1, len(events) // sample_size)
        return events[::step][:sample_size]
    if strategy == "per-pattern":
        patterns = group_by_message(events)
        selected = []
        for pattern, _count in patterns.most_common(sample_size):
            for event in events:
                from runner_support import normalize_message, event_message  # local import avoids wider API

                if normalize_message(event_message(event)) == pattern:
                    selected.append(event)
                    break
        return selected
    return events[:sample_size]


if __name__ == "__main__":
    raise SystemExit(main())
