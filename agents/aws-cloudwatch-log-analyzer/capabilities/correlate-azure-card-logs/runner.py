#!/usr/bin/env python3
"""Runner for correlate-azure-card-logs."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    clean_text,
    get_events,
    is_error_event,
    load_events_payload,
    load_fixture,
    print_error,
    render_events_table,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run aws-cloudwatch-log-analyzer/correlate-azure-card-logs")
    parser.add_argument("--azure-project")
    parser.add_argument("--work-item-id", type=int)
    parser.add_argument("--region")
    parser.add_argument("--log-group")
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--time-window-minutes", type=int, default=30)
    parser.add_argument("--include-comment-draft", action="store_true")
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


def load_payload(args: argparse.Namespace) -> dict:
    if args.fixture:
        return load_fixture(args.fixture)
    if not (args.azure_project and args.work_item_id and args.region):
        raise ValueError("--azure-project, --work-item-id and --region are required")
    if not (args.log_group and args.start_time and args.end_time):
        raise ValueError("--log-group, --start-time and --end-time are required for CloudWatch lookup")
    events_payload = load_events_payload(args)
    return {
        "card": {
            "id": args.work_item_id,
            "project": args.azure_project,
            "description": "",
        },
        "cloudwatch": events_payload,
    }


def render(payload: dict, args: argparse.Namespace) -> str:
    card = payload.get("card") or payload.get("work_item") or {}
    cloudwatch = payload.get("cloudwatch") or payload
    events = get_events(cloudwatch)
    error_events = [event for event in events if is_error_event(event)]
    extracted_log_group = args.log_group or cloudwatch.get("log_group") or extract_log_group(card)
    lines = [
        "# Azure Card Log Correlation",
        "",
        "## Card Azure",
        "",
        f"- Projeto: {value_or_dash(args.azure_project or card.get('project'))}",
        f"- Work item: {value_or_dash(args.work_item_id or card.get('id'))}",
        f"- Titulo: {value_or_dash(card.get('title'))}",
        "",
        "## Consulta CloudWatch",
        "",
        f"- Regiao: {value_or_dash(args.region or cloudwatch.get('region'))}",
        f"- Log group: {value_or_dash(extracted_log_group)}",
        f"- Eventos encontrados: {len(events)}",
        f"- Eventos de erro: {len(error_events)}",
        "",
        "## Evidencias",
        "",
        *render_events_table(events, limit=10),
        "",
        "## Analise",
        "",
        "- Os eventos CloudWatch acima foram correlacionados com os dados informados do card.",
        "- Validar causa raiz separadamente antes de mover status ou comentar conclusao definitiva.",
        "",
        "## Proximos passos",
        "",
        "- Usar `analyze-service-error` para aprofundar padroes de erro.",
        "- Usar `generate-incident-report` para consolidar relatorio de incidente.",
    ]
    if args.include_comment_draft:
        lines.extend(
            [
                "",
                "## Comentario sugerido",
                "",
                "```text",
                f"Analise de logs correlacionada ao card {value_or_dash(args.work_item_id or card.get('id'))}. Foram encontrados {len(events)} eventos na janela analisada, com {len(error_events)} eventos relevantes para erro/alerta. Validar evidencias antes de alterar status.",
                "```",
            ]
        )
    lines.extend(["", "## Escrita", "", "- Nenhuma escrita foi executada."])
    return "\n".join(lines).rstrip() + "\n"


def extract_log_group(card: dict) -> str:
    text = clean_text(card.get("description"))
    match = re.search(r"(/aws/[^\s<]+)", text)
    return match.group(1) if match else ""


if __name__ == "__main__":
    raise SystemExit(main())
