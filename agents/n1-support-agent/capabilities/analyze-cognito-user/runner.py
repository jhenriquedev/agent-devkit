#!/usr/bin/env python3
"""Runner for analyze-cognito-user."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import diagnostic_gap_payload, load_fixture, print_error, write_output  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run n1-support-agent/analyze-cognito-user")
    parser.add_argument("--cpf")
    parser.add_argument("--email")
    parser.add_argument("--phone")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    try:
        fixture = load_fixture(args.fixture) if args.fixture else {}
        cpf = args.cpf or fixture.get("cpf")
        payload = diagnostic_gap_payload(
            capability="analyze-cognito-user",
            check_id="cognito-user",
            source="cognito",
            reason="Cognito repository/agent is not configured; user enablement cannot be verified automatically.",
            cpf=cpf,
            orchestrated_agent=None,
            orchestrated_capability=None,
        )
        payload["facts"].update({"emailProvided": bool(args.email or fixture.get("email")), "phoneProvided": bool(args.phone or fixture.get("phone"))})
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render("N1 Cognito User Check", payload)
        write_output(content, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(title: str, payload: dict) -> str:
    lines = [
        f"# {title}",
        "",
        f"- Status: {payload.get('checkStatus')}",
        f"- CPF: {(payload.get('facts') or {}).get('cpfMasked') or '-'}",
        f"- Reason: {payload.get('reason')}",
        "",
        "## Diagnostic Gaps",
        "",
    ]
    lines.extend(f"- {gap['id']}: {gap['reason']}" for gap in payload.get("diagnosticGaps") or [])
    lines.extend(["", "## Contract", "", "```json", json.dumps(payload, ensure_ascii=False, indent=2), "```"])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
