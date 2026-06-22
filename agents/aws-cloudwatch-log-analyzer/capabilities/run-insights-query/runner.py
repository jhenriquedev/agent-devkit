#!/usr/bin/env python3
"""Runner for run-insights-query."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import get_repository, load_fixture, print_error, summarize, value_or_dash, write_output  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run aws-cloudwatch-log-analyzer/run-insights-query")
    parser.add_argument("--region")
    parser.add_argument("--log-group")
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--query")
    parser.add_argument("--query-id")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        payload = load_payload(args)
        write_output(render(payload, args), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def load_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.fixture:
        return load_fixture(args.fixture)
    if not args.region:
        raise ValueError("--region is required when --fixture is not provided")
    repo = get_repository()
    if args.query_id:
        return repo.get_logs_insights_query_results(region=args.region, query_id=args.query_id)
    missing = [
        name
        for name in ("log_group", "start_time", "end_time", "query")
        if not getattr(args, name, None)
    ]
    if missing:
        raise ValueError(f"missing required query scope: {', '.join(missing)}")
    return repo.start_logs_insights_query(
        region=args.region,
        log_group=args.log_group,
        start_time=args.start_time,
        end_time=args.end_time,
        query=args.query,
        limit=args.limit,
    )


def render(payload: dict[str, Any], args: argparse.Namespace) -> str:
    query_id = payload.get("query_id") or payload.get("queryId") or args.query_id
    status = payload.get("status")
    results = payload.get("results") or []
    started = bool(query_id and not status and not results)
    lines = [
        "# CloudWatch Logs Insights Query",
        "",
        "## Consulta",
        "",
        f"- Regiao: {value_or_dash(payload.get('region') or args.region)}",
        f"- Log group: {value_or_dash(payload.get('log_group') or args.log_group)}",
        f"- Inicio: {value_or_dash(payload.get('start_time') or args.start_time)}",
        f"- Fim: {value_or_dash(payload.get('end_time') or args.end_time)}",
        f"- Query id: {value_or_dash(query_id)}",
        f"- Status: {value_or_dash(status or ('Iniciada' if started else None))}",
        "",
    ]
    if args.query or payload.get("query"):
        lines.extend(["## Query", "", "```sql", str(payload.get("query") or args.query), "```", ""])
    if started:
        lines.extend(
            [
                "## Resultado",
                "",
                "- Query iniciada. Execute novamente com `--query-id` para consultar o resultado.",
            ]
        )
    else:
        lines.extend(["## Resultados", "", *render_results(results)])
    statistics = payload.get("statistics") or {}
    if statistics:
        lines.extend(["", "## Estatisticas", "", "```json", json.dumps(statistics, ensure_ascii=False, indent=2), "```"])
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Nenhuma escrita foi executada.",
            "- Trate resultados como dados sensiveis e valide hipoteses antes de concluir causa raiz.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_results(results: list[Any]) -> list[str]:
    if not results:
        return ["- Nenhum resultado disponivel."]
    lines = ["| Linha | Campos |", "|---|---|"]
    for index, row in enumerate(results[:20], start=1):
        lines.append(f"| {index} | {summarize(format_row(row), 500)} |")
    return lines


def format_row(row: Any) -> str:
    if isinstance(row, list):
        parts = []
        for item in row:
            if isinstance(item, dict):
                parts.append(f"{item.get('field', '-')}: {item.get('value', '-')}")
            else:
                parts.append(str(item))
        return "; ".join(parts)
    if isinstance(row, dict):
        return "; ".join(f"{key}: {value}" for key, value in row.items())
    return str(row)


if __name__ == "__main__":
    raise SystemExit(main())
