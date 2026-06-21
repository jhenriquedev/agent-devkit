#!/usr/bin/env python3
"""Runner for incident-report."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import count_by, get_repository, load_fixture, print_error, render_counter, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run topdesk-orchestrator/incident-report")
    parser.add_argument("--query")
    parser.add_argument("--status")
    parser.add_argument("--operator-group")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = load_fixture(args.fixture) if args.fixture else get_repository().list_incidents(query=args.query, status=args.status, operator_group=args.operator_group, limit=args.limit)
        write_output(render(payload), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(payload: dict) -> str:
    items = payload.get("items") or payload.get("incidents") or []
    lines = ["# Relatorio de Incidentes TOPdesk", "", f"- Total: {len(items)}", "", "## Por status", "", *render_counter(count_by(items, "status")), "", "## Por prioridade", "", *render_counter(count_by(items, "priority")), "", "## Sem grupo operador", ""]
    without_group = [item for item in items if not item.get("operator_group")]
    lines.extend(f"- {value_or_dash(item.get('number') or item.get('id'))}: {value_or_dash(item.get('brief_description'))}" for item in without_group[:20])
    if not without_group:
        lines.append("- Nenhum.")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
