#!/usr/bin/env python3
"""Runner for search-log-events."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    get_events,
    load_events_payload,
    print_error,
    render_events_table,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run aws-cloudwatch-log-analyzer/search-log-events")
    parser.add_argument("--region")
    parser.add_argument("--log-group")
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--filter-pattern")
    parser.add_argument("--log-stream-prefix")
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
    events = get_events(payload)
    lines = [
        "# Log Events",
        "",
        "## Consulta",
        "",
        f"- Regiao: {value_or_dash(payload.get('region') or args.region)}",
        f"- Log group: {value_or_dash(payload.get('log_group') or args.log_group)}",
        f"- Inicio: {value_or_dash(payload.get('start_time') or args.start_time)}",
        f"- Fim: {value_or_dash(payload.get('end_time') or args.end_time)}",
        f"- Filtro: {value_or_dash(payload.get('filter_pattern') or args.filter_pattern)}",
        f"- Total retornado: {len(events)}",
        f"- Next token: {value_or_dash(payload.get('next_token'))}",
        "",
        "## Amostras",
        "",
        *render_events_table(events, limit=min(args.limit, 20)),
    ]
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
