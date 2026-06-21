#!/usr/bin/env python3
"""Runner for bpo-analyser/list-proposals-by-cpf."""

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
    render_proposals_table,
    value_or_dash,
    write_payload,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bpo-analyser/list-proposals-by-cpf")
    parser.add_argument("--cpf")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()
    try:
        payload = load_fixture(args.fixture) if args.fixture else get_repository().list_proposals_by_cpf(
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
    lines = [
        "# Propostas BPO por CPF",
        "",
        f"- CPF: {value_or_dash(payload.get('masked_cpf') or mask_cpf(payload.get('cpf')))}",
        f"- Total: {value_or_dash(payload.get('count'))}",
        "",
        "## Propostas",
        "",
        *render_proposals_table(payload.get("proposals") or []),
    ]
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
