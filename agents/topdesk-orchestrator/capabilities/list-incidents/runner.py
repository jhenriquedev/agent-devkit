#!/usr/bin/env python3
"""Runner for list-incidents."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import get_repository, load_fixture, print_error, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run topdesk-orchestrator/list-incidents")
    parser.add_argument("--query")
    parser.add_argument("--status")
    parser.add_argument("--operator-group")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = load_fixture(args.fixture) if args.fixture else get_repository().list_incidents(
            query=args.query, status=args.status, operator_group=args.operator_group, limit=args.limit
        )
        write_output(render(payload, args), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(payload: dict, args: argparse.Namespace) -> str:
    items = payload.get("items") or payload.get("incidents") or []
    lines = [
        "# TOPdesk Incidents",
        "",
        "## Filtros",
        "",
        f"- Query: {value_or_dash(args.query)}",
        f"- Status: {value_or_dash(args.status)}",
        f"- Grupo operador: {value_or_dash(args.operator_group)}",
        f"- Limite: {args.limit}",
        f"- Total retornado: {len(items)}",
        "",
        "## Resultados",
        "",
        "| ID | Numero | Resumo | Status | Prioridade | Grupo |",
        "|---|---|---|---|---|---|",
    ]
    for item in items:
        lines.append(
            "| "
            + " | ".join(
                [
                    value_or_dash(item.get("id")),
                    value_or_dash(item.get("number")),
                    value_or_dash(item.get("brief_description")),
                    value_or_dash(item.get("status")),
                    value_or_dash(item.get("priority")),
                    value_or_dash(item.get("operator_group")),
                ]
            )
            + " |"
        )
    if not items:
        lines.append("| - | - | Nenhum incidente encontrado | - | - | - |")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
