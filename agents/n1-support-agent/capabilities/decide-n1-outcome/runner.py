#!/usr/bin/env python3
"""Runner for decide-n1-outcome."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from domain_knowledge import build_diagnostic_gaps, build_evidence_ledger, evaluate_quality_gate  # noqa: E402
from runner_support import decide, load_fixture, print_error, write_output  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run n1-support-agent/decide-n1-outcome")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    try:
        fixture = load_fixture(args.fixture)
        entities = fixture.get("entities") or {}
        checks = fixture.get("checks") or []
        symptom_route = fixture.get("symptomRoute") or {}
        decision = decide(entities, checks, symptom_route=symptom_route)
        diagnostic_gaps = [
            *(fixture.get("diagnosticGaps") or []),
            *build_diagnostic_gaps(checks=checks, symptom_route=symptom_route),
        ]
        payload = {
            "capability": "decide-n1-outcome",
            "status": "completed",
            "decision": decision,
            "businessRulesApplied": symptom_route.get("businessRules") or [],
            "diagnosticGaps": diagnostic_gaps,
            "qualityGate": evaluate_quality_gate(entities=entities, checks=checks, symptom_route=symptom_route),
            "evidenceLedger": build_evidence_ledger(checks=checks, symptom_route=symptom_route),
        }
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render(payload)
        write_output(content, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(payload: dict) -> str:
    decision = payload["decision"]
    lines = [
        "# N1 Decision",
        "",
        f"- Status: {decision.get('status')}",
        f"- Category: {decision.get('category')}",
        f"- Confidence: {decision.get('confidence')}",
        f"- Summary: {decision.get('summary')}",
        "",
        "## Business Rules",
        "",
    ]
    lines.extend(f"- {rule.get('id')}: {rule.get('supportImpact') or rule.get('rule')}" for rule in payload.get("businessRulesApplied") or [])
    if not payload.get("businessRulesApplied"):
        lines.append("- -")
    lines.extend(["", "## Contract", "", "```json", json.dumps(payload, ensure_ascii=False, indent=2), "```"])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
