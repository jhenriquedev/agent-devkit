#!/usr/bin/env python3
"""Runner for extract-card-entities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import extract_entities, fixture_text, load_fixture, print_error, write_output  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run n1-support-agent/extract-card-entities")
    parser.add_argument("--text")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    try:
        fixture = load_fixture(args.fixture) if args.fixture else {}
        text = args.text or fixture_text(fixture)
        entities = extract_entities(text)
        gaps = []
        if not any(entities.get(key) for key in ("cpfPresent", "proposalNumber", "requestId", "topdeskTicket")):
            gaps.append(
                {
                    "id": "missing-operational-identifier",
                    "source": "card",
                    "reason": "Card nao contem CPF, proposta, TOPdesk ou request id identificavel.",
                }
            )
        payload = {
            "capability": "extract-card-entities",
            "status": "completed",
            "entities": entities,
            "diagnosticGaps": gaps,
        }
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render(payload)
        write_output(content, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(payload: dict) -> str:
    entities = payload["entities"]
    lines = [
        "# N1 Extracted Entities",
        "",
        f"- CPF: {entities.get('cpfMasked') or '-'}",
        f"- Proposal: {entities.get('proposalNumber') or '-'}",
        f"- Contract: {entities.get('contractNumber') or '-'}",
        f"- TOPdesk: {entities.get('topdeskTicket') or '-'}",
        f"- Request ID: {entities.get('requestId') or '-'}",
        "",
        "## Diagnostic Gaps",
        "",
    ]
    lines.extend(f"- {gap['id']}: {gap['reason']}" for gap in payload.get("diagnosticGaps") or [])
    if not payload.get("diagnosticGaps"):
        lines.append("- -")
    lines.extend(["", "## Contract", "", "```json", json.dumps(payload, ensure_ascii=False, indent=2), "```"])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
