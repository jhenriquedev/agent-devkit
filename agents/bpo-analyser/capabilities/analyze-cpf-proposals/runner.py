#!/usr/bin/env python3
"""Runner for bpo-analyser/analyze-cpf-proposals."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # pylint: disable=import-error
    get_repository,
    load_fixture,
    mask_cpf,
    print_error,
    proposal_by_cpf_lines,
    render_proposals_table,
    value_or_dash,
    write_payload,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bpo-analyser/analyze-cpf-proposals")
    parser.add_argument("--cpf")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()
    try:
        payload = load_fixture(args.fixture) if args.fixture else get_repository().analyze_cpf_proposals(
            require(args.cpf, "cpf")
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
    facts = payload.get("facts") or {}
    inferences = payload.get("inferences") or {}
    attention = inferences.get("attention_points") or []
    lines = [
        "# Analise de Propostas BPO por CPF",
        "",
        "## Resumo",
        "",
        f"- CPF: {value_or_dash(payload.get('masked_cpf') or mask_cpf(payload.get('cpf')))}",
        f"- Total: {value_or_dash(facts.get('total'))}",
        f"- Elegiveis: {value_or_dash(facts.get('eligible_count'))}",
        f"- Em analise: {value_or_dash(facts.get('under_analysis_count'))}",
        f"- Reprovadas: {value_or_dash(facts.get('rejected_count'))}",
        "",
        "## Proposta mais recente aprovada/integrada",
        "",
        *proposal_by_cpf_lines(facts.get("latest_integrated_or_approved")),
        "",
        "## Todas as propostas",
        "",
        *render_proposals_table(payload.get("proposals") or []),
        "",
        "## Inferencias",
        "",
    ]
    lines.extend(f"- {item}" for item in attention) if attention else lines.append(
        "- Nenhum ponto de atencao inferido."
    )
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
