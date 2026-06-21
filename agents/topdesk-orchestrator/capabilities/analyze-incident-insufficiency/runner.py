#!/usr/bin/env python3
"""Runner for analyze-incident-insufficiency."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import analyze_insufficiency, get_repository, load_fixture, print_error, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run topdesk-orchestrator/analyze-incident-insufficiency")
    parser.add_argument("--id")
    parser.add_argument("--number")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        incident = load_fixture(args.fixture).get("incident") if args.fixture else get_repository().get_incident(incident_id=args.id, number=args.number)
        if not incident:
            raise ValueError("incident not found")
        analysis = analyze_insufficiency(incident)
        write_output(render(incident, analysis), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(incident: dict, analysis: dict) -> str:
    missing_fields = [f"- {item}" for item in analysis["missing_fields"]] or ["- Nenhum."]
    questions = [f"- {item}" for item in analysis["questions"]] or ["- Nenhuma."]
    lines = [
        "# Analise de Insuficiencia do Incidente",
        "",
        f"- Incidente: {value_or_dash(incident.get('number') or incident.get('id'))}",
        f"- Insuficiente: {analysis['is_insufficient']}",
        f"- Confianca: {analysis['confidence']}",
        "",
        "## Campos faltantes",
        "",
        *missing_fields,
        "",
        "## Perguntas sugeridas",
        "",
        *questions,
    ]
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
