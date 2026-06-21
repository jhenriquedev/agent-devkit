#!/usr/bin/env python3
"""Runner for create-incident."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import get_repository, load_fixture, print_error, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run topdesk-orchestrator/create-incident")
    parser.add_argument("--brief-description")
    parser.add_argument("--request")
    parser.add_argument("--caller-id")
    parser.add_argument("--category")
    parser.add_argument("--priority")
    parser.add_argument("--operator-group")
    parser.add_argument("--fields-json")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        fields = build_fields(args)
        result = load_fixture(args.fixture).get("result") if args.fixture else get_repository().create_incident(fields, dry_run=not args.execute)
        write_output(render(fields, result or {"dry_run": not args.execute}), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def build_fields(args: argparse.Namespace) -> dict:
    fields = json.loads(args.fields_json) if args.fields_json else {}
    if args.brief_description:
        fields["briefDescription"] = args.brief_description
    if args.request:
        fields["request"] = args.request
    if args.caller_id:
        fields["caller"] = {"id": args.caller_id}
    if args.category:
        fields["category"] = {"name": args.category}
    if args.priority:
        fields["priority"] = {"name": args.priority}
    if args.operator_group:
        fields["operatorGroup"] = {"name": args.operator_group}
    if not fields.get("briefDescription") or not fields.get("request"):
        raise ValueError("--brief-description and --request are required unless provided in --fields-json")
    return fields


def render(fields: dict, result: dict) -> str:
    return "\n".join([
        "# Criacao de Incidente TOPdesk",
        "",
        "## Payload planejado",
        "",
        f"- Resumo: {value_or_dash(fields.get('briefDescription'))}",
        f"- Request: {value_or_dash(fields.get('request'))}",
        "",
        "## Resultado",
        "",
        f"- Dry-run: {value_or_dash(result.get('dry_run'))}",
        f"- Incidente: {value_or_dash((result.get('incident') or {}).get('number'))}",
    ]).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
