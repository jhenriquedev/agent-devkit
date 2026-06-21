#!/usr/bin/env python3
"""Runner for bpo-analyser/consult-proposal."""

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
    render_observations,
    write_payload,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bpo-analyser/consult-proposal")
    parser.add_argument("--proposal-number")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()
    try:
        payload = load_fixture(args.fixture) if args.fixture else get_repository().consult_proposal(
            require(args.proposal_number, "proposal_number")
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
    lines = ["# Consulta de Proposta BPO", "", "## Fatos", "", *proposal_lines(payload)]
    lines.extend(["", "## Observacoes", "", *render_observations(payload.get("observations") or [])])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
