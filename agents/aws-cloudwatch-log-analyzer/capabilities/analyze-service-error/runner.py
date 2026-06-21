#!/usr/bin/env python3
"""Runner for analyze-service-error."""

from __future__ import annotations

import argparse
from collections import Counter
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
    print_error,
    render_counter,
    render_events_table,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run aws-cloudwatch-log-analyzer/analyze-service-error")
    parser.add_argument("--region")
    parser.add_argument("--service")
    parser.add_argument("--environment")
    parser.add_argument("--log-group")
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--error-filter", dest="filter_pattern")
    parser.add_argument("--endpoint")
    parser.add_argument("--status-code")
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
    error_events = [event for event in events if is_error_event(event)]
    status_counter = Counter(extract_status_code(event_message(event)) for event in error_events)
    endpoint_counter = Counter(extract_endpoint(event_message(event)) for event in error_events)
    hypotheses = build_hypotheses(error_events)
    lines = [
        "# Service Error Analysis",
        "",
        "## Sumario",
        "",
        f"- Servico: {value_or_dash(args.service or payload.get('service'))}",
        f"- Ambiente: {value_or_dash(args.environment or payload.get('environment'))}",
        f"- Regiao: {value_or_dash(args.region or payload.get('region'))}",
        f"- Log group: {value_or_dash(args.log_group or payload.get('log_group'))}",
        f"- Eventos analisados: {len(events)}",
        f"- Eventos de erro: {len(error_events)}",
        "",
        "## Padroes por mensagem",
        "",
        *render_counter(group_by_message(error_events)),
        "",
        "## Status codes",
        "",
        *render_counter(status_counter),
        "",
        "## Endpoints",
        "",
        *render_counter(endpoint_counter),
        "",
        "## Evidencias",
        "",
        *render_events_table(error_events, limit=10),
        "",
        "## Hipoteses",
        "",
        *[f"- {item}" for item in hypotheses],
        "",
        "## Proximos passos",
        "",
        "- Validar impacto e recorrencia antes de concluir causa raiz.",
        "- Correlacionar com deploys, metricas e eventos do ambiente.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_hypotheses(events: list[dict]) -> list[str]:
    if not events:
        return ["Nenhum evento de erro foi encontrado na amostra carregada."]
    messages = " ".join(event_message(event).lower() for event in events)
    hypotheses = []
    if "timeout" in messages:
        hypotheses.append("Ha sinais de timeout; validar dependencia externa, banco ou latencia.")
    if "5" in messages:
        hypotheses.append("Ha sinais de erro 5xx; validar saude do servico e excecoes.")
    if "health" in messages:
        hypotheses.append("Ha sinais de health warning; validar ambiente e instancias.")
    return hypotheses or ["Ha eventos de erro, mas a causa raiz nao pode ser afirmada apenas pela amostra."]


if __name__ == "__main__":
    raise SystemExit(main())
