#!/usr/bin/env python3
"""Runner for triage-incident."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import clean_text, get_repository, load_fixture, print_error, validate_update_fields, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run topdesk-orchestrator/triage-incident")
    parser.add_argument("--id")
    parser.add_argument("--number")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = load_triage_payload(args)
        incident = payload["incident"]
        suggestions = build_suggestions(incident, payload.get("catalogs") or {}, payload.get("persons") or {})
        fields = build_update_fields(suggestions)
        validate_update_fields(fields)
        result = payload.get("result") or {"dry_run": not args.execute, "target": args.id or args.number or incident.get("id"), "fields": fields}
        result.setdefault("fields", fields)
        write_output(render(incident, suggestions, fields, result), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def load_triage_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.fixture:
        fixture = load_fixture(args.fixture)
        if not fixture.get("incident"):
            raise ValueError("fixture must include incident")
        return fixture
    if not args.id and not args.number:
        raise ValueError("--id or --number is required")
    repo = get_repository()
    incident = repo.get_incident(incident_id=args.id, number=args.number)
    catalogs = {
        "categories": repo.get_catalog("categories"),
        "priorities": repo.get_catalog("priorities"),
    }
    persons = repo.search_persons(incident.get("caller"), limit=5) if incident.get("caller") else {"items": []}
    suggestions = build_suggestions(incident, catalogs, persons)
    fields = build_update_fields(suggestions)
    result = repo.update_incident(fields, incident_id=args.id, number=args.number, dry_run=not args.execute)
    return {"incident": incident, "catalogs": catalogs, "persons": persons, "result": result}


def build_suggestions(incident: dict[str, Any], catalogs: dict[str, Any], persons: dict[str, Any]) -> dict[str, dict[str, str]]:
    text = " ".join(
        clean_text(incident.get(key))
        for key in ("brief_description", "request", "category", "priority", "caller")
    ).lower()
    category = choose_category(text, catalog_names(catalogs.get("categories")))
    priority = choose_priority(text, catalog_names(catalogs.get("priorities")))
    caller = choose_person(clean_text(incident.get("caller")), persons.get("items") or [])
    return {
        "category": {
            "value": category or "",
            "confidence": "media" if category else "baixa",
            "reason": "Termos do incidente apontam para sistema/software." if category else "Sem categoria de catalogo sustentada por evidencia.",
        },
        "priority": {
            "value": priority or "",
            "confidence": "media" if priority else "baixa",
            "reason": "Prioridade derivada de impacto textual e catalogo informado." if priority else "Impacto e urgencia insuficientes para prioridade segura.",
        },
        "caller": {
            "value": caller.get("id") or "",
            "confidence": "media" if caller else "baixa",
            "reason": f"Solicitante resolvido por nome: {caller.get('name') or caller.get('displayName')}." if caller else "Solicitante nao resolvido em persons.",
        },
    }


def catalog_names(catalog: Any) -> list[str]:
    items = (catalog or {}).get("items") if isinstance(catalog, dict) else []
    names = []
    for item in items or []:
        if isinstance(item, dict):
            name = item.get("name") or item.get("value")
        else:
            name = str(item)
        if name:
            names.append(str(name))
    return names


def choose_category(text: str, categories: list[str]) -> str | None:
    if not categories:
        return None
    signals = {
        "Software": ("portal", "sistema", "software", "erro", "503", "aplicacao"),
        "Acesso": ("acesso", "login", "autenticar", "senha"),
        "Hardware": ("notebook", "computador", "impressora", "hardware"),
    }
    for preferred, terms in signals.items():
        if any(term in text for term in terms):
            match = find_catalog_match(preferred, categories)
            if match:
                return match
    return None


def choose_priority(text: str, priorities: list[str]) -> str | None:
    if not priorities:
        return None
    if any(term in text for term in ("operacao critica", "indisponivel geral", "todos usuarios", "producao parada")):
        return find_catalog_match("P1", priorities) or priorities[0]
    if any(term in text for term in ("equipe", "setor", "financeira", "varios usuarios", "indisponivel")):
        return find_catalog_match("P2", priorities) or priorities[0]
    if any(term in text for term in ("usuario", "individual", "uma pessoa")):
        return find_catalog_match("P3", priorities) or priorities[-1]
    if any(term in text for term in ("duvida", "melhoria", "baixo impacto", "solicitacao comum")):
        return find_catalog_match("P4", priorities) or priorities[-1]
    return None


def find_catalog_match(expected: str, values: list[str]) -> str | None:
    expected_lower = expected.lower()
    for value in values:
        if value.lower() == expected_lower:
            return value
    for value in values:
        if expected_lower in value.lower():
            return value
    return None


def choose_person(caller_name: str, persons: list[Any]) -> dict[str, Any]:
    normalized_caller = caller_name.lower()
    for person in persons:
        if not isinstance(person, dict):
            continue
        name = clean_text(person.get("name") or person.get("displayName") or person.get("dynamicName"))
        if name and (name.lower() == normalized_caller or normalized_caller in name.lower()):
            return person
    return {}


def build_update_fields(suggestions: dict[str, dict[str, str]]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if suggestions["category"]["value"]:
        fields["category"] = {"name": suggestions["category"]["value"]}
    if suggestions["priority"]["value"]:
        fields["priority"] = {"name": suggestions["priority"]["value"]}
    if suggestions["caller"]["value"]:
        fields["caller"] = {"id": suggestions["caller"]["value"]}
    return fields


def render(incident: dict[str, Any], suggestions: dict[str, dict[str, str]], fields: dict[str, Any], result: dict[str, Any]) -> str:
    lines = [
        "# Triagem de Incidente TOPdesk",
        "",
        "## Fatos (TOPdesk)",
        "",
        f"- Incidente: {value_or_dash(incident.get('number') or incident.get('id'))}",
        f"- Resumo: {value_or_dash(incident.get('brief_description'))}",
        f"- Solicitante: {value_or_dash(incident.get('caller'))}",
        "",
        "## Inferencias (agente)",
        "",
    ]
    for key, item in suggestions.items():
        lines.append(f"- {key}: {value_or_dash(item.get('value'))} ({item.get('confidence')}) - {item.get('reason')}")
    lines.extend(
        [
            "",
            "## Plano de update",
            "",
            "```json",
            json.dumps(fields, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Proxima acao",
            "",
            f"- Dry-run: {value_or_dash(result.get('dry_run'))}",
            "- Reexecute com `--execute` para aplicar." if result.get("dry_run") else "- Atualizacao executada.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
