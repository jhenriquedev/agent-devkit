#!/usr/bin/env python3
"""Runner for request-more-info."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import analyze_insufficiency, get_repository, load_fixture, print_error, validate_update_fields, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run topdesk-orchestrator/request-more-info")
    parser.add_argument("--id")
    parser.add_argument("--number")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        repo = None if args.fixture else get_repository()
        incident = load_fixture(args.fixture).get("incident") if args.fixture else repo.get_incident(incident_id=args.id, number=args.number)
        analysis = analyze_insufficiency(incident)
        if not analysis["questions"]:
            result = {"dry_run": False, "fields": {}, "skipped": True, "reason": "Nenhuma lacuna de informacao identificada."}
            write_output(render(incident, analysis, result), args.output)
            return 0
        message = "Informacoes necessarias:\n" + "\n".join(f"- {q}" for q in analysis["questions"])
        fields = {"action": message}
        validate_update_fields(fields)
        result = {"dry_run": not args.execute, "fields": fields} if args.fixture else repo.update_incident(fields, incident_id=args.id, number=args.number, dry_run=not args.execute)
        write_output(render(incident, analysis, result), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(incident: dict, analysis: dict, result: dict) -> str:
    fields = result.get("fields") or {}
    lines = [
        "# Pedido de Mais Informacoes",
        "",
        f"- Incidente: {value_or_dash(incident.get('number') or incident.get('id'))}",
        f"- Dry-run: {value_or_dash(result.get('dry_run'))}",
    ]
    if result.get("skipped"):
        lines.extend(["", "## Resultado", "", f"- {value_or_dash(result.get('reason'))}"])
        return "\n".join(lines).rstrip() + "\n"
    lines.extend(
        [
            "",
            "## Payload planejado",
            "",
            "```json",
            json.dumps(fields, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Perguntas",
            "",
        ]
    )
    lines.extend(f"- {q}" for q in analysis["questions"])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
