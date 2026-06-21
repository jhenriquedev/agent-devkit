#!/usr/bin/env python3
"""End-to-end runner for the gerar-relatorio-cards capability."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    clean_text,
    format_tags,
    get_attachments,
    get_repository,
    load_fixture,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run azure-devops-orchestrator/gerar-relatorio-cards"
    )
    parser.add_argument("--project")
    parser.add_argument("--wiql")
    parser.add_argument("--state")
    parser.add_argument("--assigned-to")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--include-comments", action="store_true")
    parser.add_argument("--include-details", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        payload = load_report_payload(args)
        markdown = render_report(payload, args)
        write_output(markdown, args.output)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


def load_report_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.fixture:
        data = load_fixture(args.fixture)
        if "cards" not in data:
            raise ValueError("fixture must contain 'cards'")
        return {
            "project": data.get("project") or args.project,
            "wiql": data.get("wiql", ""),
            "cards": data.get("cards") or [],
            "limit": data.get("limit", args.limit),
            "list_count": data.get("list_count", len(data.get("cards") or [])),
            "filters": data.get("filters", {}),
        }

    if not args.project:
        raise ValueError("--project is required when --fixture is not provided")

    repo = get_repository()
    listing = repo.list_work_items(
        project=args.project,
        wiql=args.wiql,
        state=args.state,
        assigned_to=args.assigned_to,
        tags=args.tag,
        limit=args.limit,
    )
    cards = []
    for item in listing.get("items", []) or []:
        work_item_id = item.get("id")
        if work_item_id is None:
            continue
        card: dict[str, Any] = {
            "work_item": repo.get_work_item(
                int(work_item_id),
                project=args.project,
                expand_relations=True,
            )
        }
        if args.include_comments:
            card["comments"] = repo.get_work_item_comments(int(work_item_id), project=args.project)
        cards.append(card)

    return {
        "project": args.project,
        "wiql": listing.get("wiql", ""),
        "cards": cards,
        "limit": args.limit,
        "list_count": listing.get("count", len(cards)),
        "filters": {
            "state": args.state,
            "assigned_to": args.assigned_to,
            "tags": args.tag,
        },
    }


def render_report(payload: dict[str, Any], args: argparse.Namespace) -> str:
    cards = normalize_cards(payload.get("cards") or [])
    summary = build_summary(cards)
    filters = payload.get("filters") or {}
    limit = int(payload.get("limit") or args.limit)
    hit_limit = len(cards) >= limit and bool(cards)

    lines = [
        "# Relatorio de Cards Azure DevOps",
        "",
        "## Consulta",
        "",
        f"- Projeto: {value_or_dash(payload.get('project') or args.project)}",
        f"- WIQL: {value_or_dash(args.wiql or payload.get('wiql'))}",
        f"- Estado: {value_or_dash(args.state or filters.get('state'))}",
        f"- Responsavel: {value_or_dash(args.assigned_to or filters.get('assigned_to'))}",
        f"- Tags: {format_tags(args.tag or filters.get('tags') or [])}",
        f"- Limite: {limit}",
        f"- Comentarios incluidos: {value_or_dash(args.include_comments)}",
        f"- Detalhes incluidos: {value_or_dash(args.include_details)}",
        "",
        "## Sumario Executivo",
        "",
        f"- Total de cards: {summary['total']}",
        f"- Sem responsavel: {len(summary['sem_responsavel'])}",
        f"- Sem criterios: {len(summary['sem_criterios'])}",
        f"- Sem descricao: {len(summary['sem_descricao'])}",
        f"- Com anexos: {len(summary['com_anexos'])}",
        f"- Com comentarios: {len(summary['com_comentarios'])}",
        f"- Consulta atingiu o limite: {value_or_dash(hit_limit)}",
        "",
        "### Por estado",
        "",
        *render_counter(summary["por_estado"]),
        "",
        "### Por responsavel",
        "",
        *render_counter(summary["por_responsavel"]),
        "",
        "## Tabela Consolidada",
        "",
        "| ID | Tipo | Titulo | Estado | Coluna | Responsavel | Tags | Comentarios | Anexos |",
        "|---|---|---|---|---|---|---|---|---|",
        *render_table_rows(cards),
        "",
        "## Lacunas Operacionais",
        "",
        *render_gaps(summary),
    ]
    if hit_limit:
        lines.extend(["", "## Avisos", "", "- O retorno atingiu o limite informado; podem existir mais cards."])
    if args.include_details:
        lines.extend(["", "## Detalhes por Card", ""])
        for card in cards:
            lines.extend(render_card_detail(card))
    lines.extend(["", "## Escrita", "", "- Nenhuma escrita foi executada."])
    return "\n".join(lines).rstrip() + "\n"


def normalize_cards(raw_cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards = []
    for raw in raw_cards:
        if "work_item" in raw:
            work_item = raw.get("work_item") or {}
            comments = raw.get("comments") or {}
        else:
            work_item = raw
            comments = raw.get("comments") or {}
        comment_list = comments.get("comments", comments if isinstance(comments, list) else [])
        cards.append({"work_item": work_item, "comments": comment_list or []})
    return cards


def build_summary(cards: list[dict[str, Any]]) -> dict[str, Any]:
    por_estado: Counter[str] = Counter()
    por_responsavel: Counter[str] = Counter()
    sem_responsavel = []
    sem_criterios = []
    sem_descricao = []
    com_anexos = []
    com_comentarios = []
    for card in cards:
        work_item = card["work_item"]
        work_item_id = work_item.get("id")
        por_estado[value_or_dash(work_item.get("state"))] += 1
        por_responsavel[value_or_dash(work_item.get("assigned_to"))] += 1
        if not work_item.get("assigned_to"):
            sem_responsavel.append(work_item_id)
        if not clean_text(work_item.get("acceptance_criteria")):
            sem_criterios.append(work_item_id)
        if not clean_text(work_item.get("description")):
            sem_descricao.append(work_item_id)
        if get_attachments(work_item):
            com_anexos.append(work_item_id)
        if card.get("comments"):
            com_comentarios.append(work_item_id)
    return {
        "total": len(cards),
        "por_estado": por_estado,
        "por_responsavel": por_responsavel,
        "sem_responsavel": sem_responsavel,
        "sem_criterios": sem_criterios,
        "sem_descricao": sem_descricao,
        "com_anexos": com_anexos,
        "com_comentarios": com_comentarios,
    }


def render_counter(counter: Counter[str]) -> list[str]:
    if not counter:
        return ["- Nenhum item."]
    return [f"- {key}: {count}" for key, count in sorted(counter.items())]


def render_table_rows(cards: list[dict[str, Any]]) -> list[str]:
    if not cards:
        return ["| - | - | Nenhum card encontrado | - | - | - | - | - | - |"]
    rows = []
    for card in cards:
        work_item = card["work_item"]
        rows.append(
            "| "
            + " | ".join(
                [
                    value_or_dash(work_item.get("id")),
                    value_or_dash(work_item.get("work_item_type")),
                    clean_text(work_item.get("title")) or "-",
                    value_or_dash(work_item.get("state")),
                    value_or_dash(work_item.get("board_column")),
                    value_or_dash(work_item.get("assigned_to")),
                    format_tags(work_item.get("tags") or []),
                    str(len(card.get("comments") or [])),
                    str(len(get_attachments(work_item))),
                ]
            )
            + " |"
        )
    return rows


def render_gaps(summary: dict[str, Any]) -> list[str]:
    return [
        f"- Cards sem responsavel: {format_ids(summary['sem_responsavel'])}",
        f"- Cards sem criterios: {format_ids(summary['sem_criterios'])}",
        f"- Cards sem descricao: {format_ids(summary['sem_descricao'])}",
    ]


def render_card_detail(card: dict[str, Any]) -> list[str]:
    work_item = card["work_item"]
    comments = card.get("comments") or []
    attachments = get_attachments(work_item)
    return [
        f"### Card {value_or_dash(work_item.get('id'))} - {value_or_dash(work_item.get('title'))}",
        "",
        f"- Tipo: {value_or_dash(work_item.get('work_item_type'))}",
        f"- Estado: {value_or_dash(work_item.get('state'))}",
        f"- Coluna: {value_or_dash(work_item.get('board_column'))}",
        f"- Criado em: {value_or_dash(work_item.get('created_date'))}",
        f"- Alterado em: {value_or_dash(work_item.get('changed_date'))}",
        f"- Responsavel: {value_or_dash(work_item.get('assigned_to'))}",
        f"- Tags: {format_tags(work_item.get('tags') or [])}",
        f"- Comentarios: {len(comments)}",
        f"- Anexos: {len(attachments)}",
        f"- URL: {value_or_dash(work_item.get('url'))}",
        "",
        f"Resumo: {summarize(work_item.get('description'))}",
        "",
    ]


def summarize(value: Any, limit: int = 500) -> str:
    text = clean_text(value)
    if not text:
        return "-"
    return text[:limit] + ("..." if len(text) > limit else "")


def format_ids(values: list[Any]) -> str:
    valid = [str(value) for value in values if value is not None]
    return ", ".join(valid) if valid else "-"


if __name__ == "__main__":
    raise SystemExit(main())
