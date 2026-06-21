#!/usr/bin/env python3
"""Runner for update-incident."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import get_repository, load_fixture, print_error, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run topdesk-orchestrator/update-incident")
    parser.add_argument("--id")
    parser.add_argument("--number")
    parser.add_argument("--fields-json", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        fields = json.loads(args.fields_json)
        if not args.fixture and not (args.id or args.number):
            raise ValueError("--id or --number is required")
        result = load_fixture(args.fixture).get("result") if args.fixture else get_repository().update_incident(fields, incident_id=args.id, number=args.number, dry_run=not args.execute)
        write_output(render(args, fields, result or {"dry_run": not args.execute}), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(args: argparse.Namespace, fields: dict, result: dict) -> str:
    return "\n".join([
        "# Atualizacao de Incidente TOPdesk",
        "",
        f"- Alvo: {value_or_dash(args.id or args.number or result.get('target'))}",
        f"- Campos: {', '.join(fields.keys())}",
        f"- Dry-run: {value_or_dash(result.get('dry_run'))}",
        "",
        "Reexecute com `--execute` para aplicar." if result.get("dry_run") else "Atualizacao executada.",
    ]).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
