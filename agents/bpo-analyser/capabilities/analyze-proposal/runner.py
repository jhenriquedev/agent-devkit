#!/usr/bin/env python3
"""Runner for bpo-analyser/analyze-proposal."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (
    get_repository,
    load_fixture,
    print_error,
    proposal_lines,
    render_documents_table,
    render_observations,
    value_or_dash,
    write_payload,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bpo-analyser/analyze-proposal")
    parser.add_argument("--proposal-number")
    parser.add_argument("--document-type")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()
    try:
        payload = load_fixture(args.fixture) if args.fixture else get_repository().analyze_proposal(
            require(args.proposal_number, "proposal_number"),
            document_type=args.document_type,
        )
        write_payload(payload, render, args.output, args.format)
    except Exception as exc:
        return print_error(exc)
    return 0


def require(value: str | None, name: str) -> str:
    if not value:
        raise ValueError(f"{name} is required")
    return value


def render(payload: dict) -> str:
    proposal = payload.get("proposal") or {}
    documents = payload.get("documents") or {}
    facts = payload.get("facts") or {}
    inferences = payload.get("inferences") or {}
    attention = inferences.get("attention_points") or []
    lines = [
        "# Analise de Proposta BPO",
        "",
        "## Resumo",
        "",
        f"- Proposta: {value_or_dash(facts.get('proposal_number'))}",
        f"- Situacao: {value_or_dash(facts.get('situation'))}",
        f"- Atividade: {value_or_dash(facts.get('activity'))}",
        f"- Observacoes: {value_or_dash(facts.get('observation_count'))}",
        f"- Documentos: {value_or_dash(facts.get('document_count'))}",
        f"- Tipos de documento: {', '.join(facts.get('document_types') or []) or '-'}",
        "",
        "## Fatos da Proposta",
        "",
        *proposal_lines(proposal),
        "",
        "## Observacoes",
        "",
        *render_observations(proposal.get("observations") or []),
        "",
        "## Documentos",
        "",
        *render_documents_table(documents.get("files") or []),
        "",
        "## Inferencias",
        "",
    ]
    if attention:
        lines.extend(f"- {item}" for item in attention)
    else:
        lines.append("- Nenhum ponto de atencao inferido.")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
