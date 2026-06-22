#!/usr/bin/env python3
"""Runner for generate-n1-artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import build_artifacts, load_fixture, print_error, write_output  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run n1-support-agent/generate-n1-artifacts")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    try:
        fixture = load_fixture(args.fixture)
        card = fixture.get("card") or {}
        entities = fixture.get("entities") or {}
        decision = fixture.get("decision") or {
            "status": "needs_more_info",
            "category": "insufficient_input",
            "confidence": 0.0,
            "summary": "Contrato parcial nao trouxe decisao N1.",
        }
        checks = fixture.get("checks") or []
        payload = {
            "capability": "generate-n1-artifacts",
            "status": "completed",
            "artifacts": build_artifacts(card, entities, decision, checks),
        }
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render(payload)
        write_output(content, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(payload: dict) -> str:
    artifacts = payload["artifacts"]
    lines = [
        "# N1 Artifacts",
        "",
        "## Internal Comment",
        "",
        artifacts.get("internalComment") or "-",
        "",
        "## Customer Reply",
        "",
        artifacts.get("customerReply") or "-",
        "",
        "## N2 Escalation",
        "",
        artifacts.get("n2Escalation") or "-",
        "",
        "## Contract",
        "",
        "```json",
        json.dumps(payload, ensure_ascii=False, indent=2),
        "```",
    ]
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
