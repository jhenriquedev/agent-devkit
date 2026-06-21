#!/usr/bin/env python3
"""Runner for generate-incident-report."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    event_message,
    get_events,
    group_by_message,
    is_error_event,
    load_events_payload,
    print_error,
    render_counter,
    render_events_table,
    sort_events,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run aws-cloudwatch-log-analyzer/generate-incident-report")
    parser.add_argument("--region")
    parser.add_argument("--service")
    parser.add_argument("--environment")
    parser.add_argument("--log-group")
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--incident-title")
    parser.add_argument("--filter-pattern")
    parser.add_argument("--include-samples", action="store_true")
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
    events = sort_events(get_events(payload))
    error_events = [event for event in events if is_error_event(event)]
    title = args.incident_title or payload.get("incident_title") or "CloudWatch Logs incident report"
    lines = [
        "# Incident Report",
        "",
        "## Sumario Executivo",
        "",
        f"- Titulo: {value_or_dash(title)}",
        f"- Servico: {value_or_dash(args.service or payload.get('service'))}",
        f"- Ambiente: {value_or_dash(args.environment or payload.get('environment'))}",
        f"- Regiao: {value_or_dash(args.region or payload.get('region'))}",
        f"- Log group: {value_or_dash(args.log_group or payload.get('log_group'))}",
        f"- Eventos analisados: {len(events)}",
        f"- Eventos de erro: {len(error_events)}",
        "",
        "## Timeline",
        "",
        *render_events_table(events, limit=20),
        "",
        "## Evidencias",
        "",
        *render_counter(group_by_message(error_events)),
        "",
        "## Hipoteses",
        "",
        *build_hypotheses(error_events),
        "",
        "## Lacunas",
        "",
        "- Validar impacto de negocio fora dos logs antes de comunicar causa ou severidade.",
        "- Validar deploys, metricas e eventos de infraestrutura na mesma janela.",
        "",
        "## Proximos passos",
        "",
        "- Correlacionar com metricas e traces quando disponivel.",
        "- Registrar evidencias relevantes no card de sustentacao.",
    ]
    if args.include_samples:
        lines.extend(["", "## Amostras", "", *render_events_table(error_events, limit=5)])
    return "\n".join(lines).rstrip() + "\n"


def build_hypotheses(error_events: list[dict]) -> list[str]:
    if not error_events:
        return ["- Nao foram encontrados eventos de erro na amostra."]
    text = " ".join(event_message(event).lower() for event in error_events)
    hypotheses = []
    if "timeout" in text:
        hypotheses.append("- Pode existir degradacao de dependencia ou latencia.")
    if "health" in text:
        hypotheses.append("- Pode existir degradacao de health do ambiente.")
    if not hypotheses:
        hypotheses.append("- Existem erros, mas a causa raiz ainda precisa de validacao.")
    return hypotheses


if __name__ == "__main__":
    raise SystemExit(main())
