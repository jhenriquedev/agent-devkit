#!/usr/bin/env python3
"""Shared helpers for TOPdesk Orchestrator capability runners."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from html import unescape
from pathlib import Path
from typing import Any


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
TOPDESK_DIR = AGENT_DIR / "infra" / "integrations" / "topdesk"


def load_fixture(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_repository() -> Any:
    sys.path.insert(0, str(TOPDESK_DIR))
    from topdesk_repository import TopdeskRepository  # pylint: disable=import-error

    return TopdeskRepository()


def write_output(markdown: str, output: str | None) -> None:
    if output:
        Path(output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)


def print_error(exc: Exception) -> int:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(unescape(text).split())


def value_or_dash(value: Any) -> str:
    text = clean_text(value)
    return text if text else "-"


def incident_summary(incident: dict[str, Any]) -> list[str]:
    return [
        f"- ID: {value_or_dash(incident.get('id'))}",
        f"- Numero: {value_or_dash(incident.get('number'))}",
        f"- Resumo: {value_or_dash(incident.get('brief_description'))}",
        f"- Status: {value_or_dash(incident.get('status'))}",
        f"- Categoria: {value_or_dash(incident.get('category'))}",
        f"- Prioridade: {value_or_dash(incident.get('priority'))}",
        f"- Grupo operador: {value_or_dash(incident.get('operator_group'))}",
        f"- Operador: {value_or_dash(incident.get('operator'))}",
        f"- Solicitante: {value_or_dash(incident.get('caller'))}",
    ]


def analyze_insufficiency(incident: dict[str, Any]) -> dict[str, Any]:
    text = f"{clean_text(incident.get('brief_description'))}\n{clean_text(incident.get('request'))}".lower()
    missing = []
    questions = []
    if len(clean_text(incident.get("brief_description"))) < 8:
        missing.append("briefDescription")
        questions.append("Descreva em uma frase qual problema ou solicitacao precisa ser atendida.")
    if len(clean_text(incident.get("request"))) < 20:
        missing.append("request")
        questions.append("Informe o contexto, o que foi tentado e qual resultado esperado.")
    if not clean_text(incident.get("category")):
        missing.append("category")
        questions.append("Qual sistema, servico ou area esta relacionada ao chamado?")
    if not clean_text(incident.get("priority")):
        missing.append("priority")
        questions.append("Isso impacta apenas voce, uma equipe ou uma operacao critica?")
    if is_vague(text):
        missing.append("specificEvidence")
        questions.append("Existe mensagem de erro, print, numero de pedido ou identificador do ativo?")
    unique_missing = list(dict.fromkeys(missing))
    unique_questions = list(dict.fromkeys(questions))
    return {
        "is_insufficient": bool(unique_missing),
        "missing_fields": unique_missing,
        "questions": unique_questions,
        "confidence": min(0.95, 0.45 + len(unique_missing) * 0.1),
    }


def is_vague(text: str) -> bool:
    terms = ["nao funciona", "não funciona", "erro", "problema", "ajuda", "acesso", "travou"]
    return len(text) < 100 and any(term in text for term in terms)


def count_by(items: list[dict[str, Any]], field: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for item in items:
        counter[value_or_dash(item.get(field))] += 1
    return counter


def render_counter(counter: Counter[str]) -> list[str]:
    if not counter:
        return ["- Nenhum item."]
    return [f"- {key}: {count}" for key, count in sorted(counter.items())]
