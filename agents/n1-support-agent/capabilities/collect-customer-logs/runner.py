#!/usr/bin/env python3
"""Runner for collect-customer-logs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import diagnostic_gap_payload, load_fixture, print_error, write_output  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run n1-support-agent/collect-customer-logs")
    parser.add_argument("--cpf")
    parser.add_argument("--request-id")
    parser.add_argument("--correlation-id")
    parser.add_argument("--from-time")
    parser.add_argument("--to-time")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    try:
        fixture = load_fixture(args.fixture) if args.fixture else {}
        cpf = args.cpf or fixture.get("cpf")
        request_id = args.request_id or args.correlation_id or fixture.get("requestId") or fixture.get("correlationId")
        payload = diagnostic_gap_payload(
            capability="collect-customer-logs",
            check_id="customer-logs",
            source="customer-logs",
            reason="Log source, query pattern, and time window are not configured; runtime errors cannot be verified automatically.",
            cpf=cpf,
            request_id=request_id,
            orchestrated_agent="elasticsearch-log-analyzer",
            orchestrated_capability="search-log-events",
        )
        payload["facts"].update({"fromTime": args.from_time or fixture.get("fromTime"), "toTime": args.to_time or fixture.get("toTime")})
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render("N1 Customer Logs Check", payload)
        write_output(content, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(title: str, payload: dict) -> str:
    facts = payload.get("facts") or {}
    lines = [
        f"# {title}",
        "",
        f"- Status: {payload.get('checkStatus')}",
        f"- CPF: {facts.get('cpfMasked') or '-'}",
        f"- Request ID: {facts.get('requestId') or '-'}",
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
