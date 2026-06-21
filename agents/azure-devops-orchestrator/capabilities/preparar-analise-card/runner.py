#!/usr/bin/env python3
"""End-to-end runner for the preparar-analise-card capability."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    clean_text,
    format_tags,
    get_attachments,
    load_work_item_payload,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run azure-devops-orchestrator/preparar-analise-card"
    )
    parser.add_argument("--id", type=int, dest="work_item_id")
    parser.add_argument("--project")
    parser.add_argument("--analysis-type", default="sustentacao")
    parser.add_argument("--include-comment-draft", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        if not args.work_item_id and not args.fixture:
            raise ValueError("--id is required when --fixture is not provided")
        payload = load_work_item_payload(
            fixture=args.fixture,
            project=args.project,
            work_item_id=args.work_item_id or 0,
            include_comments=True,
        )
        markdown = render_analysis(payload, args)
        write_output(markdown, args.output)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


def render_analysis(payload: dict[str, Any], args: argparse.Namespace) -> str:
    work_item = payload["work_item"]
    comments = (payload.get("comments") or {}).get("comments", [])
    demand_type = classify_demand(work_item)
    gaps = identify_gaps(work_item, comments)
    hypotheses = build_hypotheses(work_item, demand_type)
    next_steps = build_next_steps(work_item, gaps, demand_type)

    lines = [
        "# Analise Operacional do Card",
        "",
        "## Sumario",
        "",
        f"- Card: {value_or_dash(work_item.get('id'))}",
        f"- Titulo: {value_or_dash(work_item.get('title'))}",
        f"- Tipo identificado: {demand_type}",
        f"- Status atual: {value_or_dash(work_item.get('state'))}",
        f"- Coluna atual: {value_or_dash(work_item.get('board_column'))}",
        f"- Responsavel: {value_or_dash(work_item.get('assigned_to'))}",
        f"- Tags: {format_tags(work_item.get('tags') or [])}",
        "",
        "## Fatos coletados",
        "",
        f"- Work item type: {value_or_dash(work_item.get('work_item_type'))}",
        f"- Criado em: {value_or_dash(work_item.get('created_date'))}",
        f"- Alterado em: {value_or_dash(work_item.get('changed_date'))}",
        f"- Comentarios carregados: {len(comments)}",
        f"- Anexos carregados: {len(get_attachments(work_item))}",
        "",
        "## Evidencias",
        "",
        f"- Descricao: {summarize_description(work_item.get('description'))}",
        "",
        "## Hipoteses",
        "",
        *[f"- {item}" for item in hypotheses],
        "",
        "## Lacunas",
        "",
        *[f"- {item}" for item in gaps],
        "",
        "## Proximos passos",
        "",
        *[f"- {item}" for item in next_steps],
    ]
    if args.include_comment_draft:
        lines.extend(["", "## Comentario sugerido", "", "```text", build_comment_draft(work_item, gaps), "```"])
        lines.extend(["", "Publicacao: use `comentar-card` para publicar apos revisao."])
    lines.extend(["", "## Escrita", "", "- Nenhuma escrita foi executada."])
    return "\n".join(lines).rstrip() + "\n"


def classify_demand(work_item: dict[str, Any]) -> str:
    text = " ".join(
        [
            clean_text(work_item.get("title")),
            clean_text(work_item.get("description")),
            " ".join(work_item.get("tags") or []),
        ]
    ).lower()
    if any(term in text for term in ["warning", "erro", "error", "exception", "bugfix"]):
        return "bug/incidente"
    if any(term in text for term in ["suporte", "sustentacao", "monitoramento"]):
        return "sustentacao"
    if any(term in text for term in ["melhoria", "feature"]):
        return "melhoria"
    return "triagem"


def identify_gaps(work_item: dict[str, Any], comments: list[dict[str, Any]]) -> list[str]:
    gaps = []
    if not clean_text(work_item.get("acceptance_criteria")):
        gaps.append("Criterios de aceite ausentes.")
    if not clean_text(work_item.get("description")):
        gaps.append("Descricao ausente ou vazia.")
    if not work_item.get("assigned_to"):
        gaps.append("Responsavel nao definido.")
    if not comments:
        gaps.append("Nenhum comentario carregado.")
    return gaps or ["Nenhuma lacuna evidente nos dados carregados."]


def build_hypotheses(work_item: dict[str, Any], demand_type: str) -> list[str]:
    description = clean_text(work_item.get("description")).lower()
    hypotheses = []
    if "elastic beanstalk" in description or "health" in description:
        hypotheses.append("Pode haver degradacao ou evento recente no ambiente Elastic Beanstalk.")
    if "cloudwatch" in description or "log group" in description:
        hypotheses.append("Ha evidencia operacional em logs que deve ser validada antes de concluir causa raiz.")
    if demand_type == "bug/incidente":
        hypotheses.append("A demanda deve ser tratada como investigacao ate existir evidencia de correcao.")
    return hypotheses or ["Nao ha hipotese tecnica forte apenas com os dados carregados."]


def build_next_steps(
    work_item: dict[str, Any],
    gaps: list[str],
    demand_type: str,
) -> list[str]:
    steps = ["Validar fatos do card antes de executar qualquer escrita."]
    if "Responsavel nao definido." in gaps:
        steps.append("Definir responsavel com `atribuir-card` quando houver dono claro.")
    if "Criterios de aceite ausentes." in gaps:
        steps.append("Pedir ou registrar criterio de aceite antes de fechar o card.")
    if demand_type == "bug/incidente":
        steps.append("Coletar evidencia operacional e confirmar impacto antes de mover status.")
    if work_item.get("state"):
        steps.append("Usar `mover-card` apenas depois de validar estado alvo e motivo.")
    return steps


def summarize_description(description: Any) -> str:
    text = clean_text(description)
    if not text:
        return "-"
    return text[:900] + ("..." if len(text) > 900 else "")


def build_comment_draft(work_item: dict[str, Any], gaps: list[str]) -> str:
    title = value_or_dash(work_item.get("title"))
    gap_text = "; ".join(gaps)
    return (
        f"Analise inicial do card `{title}` realizada. "
        f"Lacunas identificadas: {gap_text}. "
        "Proximo passo recomendado: validar evidencias e definir encaminhamento antes de alterar o status."
    )


if __name__ == "__main__":
    raise SystemExit(main())
