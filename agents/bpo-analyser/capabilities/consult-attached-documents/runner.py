#!/usr/bin/env python3
"""Runner for bpo-analyser/consult-attached-documents."""

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
    render_documents_table,
    value_or_dash,
    write_payload,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bpo-analyser/consult-attached-documents")
    parser.add_argument("--proposal-number")
    parser.add_argument("--document-type")
    parser.add_argument("--include-content", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()
    try:
        payload = load_fixture(args.fixture) if args.fixture else get_repository().consult_attached_documents(
            require(args.proposal_number, "proposal_number"),
            document_type=args.document_type,
            include_content=args.include_content,
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
    processing = payload.get("processing_status") or {}
    lines = [
        "# Documentos Anexados BPO",
        "",
        f"- Proposta: {value_or_dash(payload.get('proposal_number'))}",
        f"- Tipo solicitado: {value_or_dash(payload.get('requested_document_type'))}",
        f"- Status processamento: {value_or_dash(processing.get('status'))}",
        f"- Erro processamento: {value_or_dash(processing.get('error_message'))}",
        f"- Total: {value_or_dash(payload.get('count'))}",
        "",
        "## Arquivos",
        "",
        *render_documents_table(payload.get("files") or []),
    ]
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
