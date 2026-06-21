#!/usr/bin/env python3
"""Runner for read-incident."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import get_repository, incident_summary, load_fixture, print_error, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run topdesk-orchestrator/read-incident")
    parser.add_argument("--id")
    parser.add_argument("--number")
    parser.add_argument("--include-progress-trail", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = load_payload(args)
        write_output(render(payload), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def load_payload(args: argparse.Namespace) -> dict:
    if args.fixture:
        return load_fixture(args.fixture)
    if not args.id and not args.number:
        raise ValueError("--id or --number is required")
    repo = get_repository()
    payload = {"incident": repo.get_incident(incident_id=args.id, number=args.number)}
    if args.include_progress_trail:
        payload["progress_trail"] = repo.get_progress_trail(incident_id=args.id, number=args.number)
    return payload


def render(payload: dict) -> str:
    incident = payload.get("incident") or payload
    entries = (payload.get("progress_trail") or {}).get("entries") or []
    lines = ["# TOPdesk Incident", "", "## Identificacao", "", *incident_summary(incident), "", "## Solicitacao", "", value_or_dash(incident.get("request")), "", "## Progress trail", ""]
    if entries:
        for entry in entries[:20]:
            lines.append(f"- {value_or_dash(entry.get('date') or entry.get('creationDate'))}: {value_or_dash(entry.get('memoText') or entry.get('text'))}")
    else:
        lines.append("- Nenhum historico carregado.")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
