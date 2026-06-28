#!/usr/bin/env python3
"""Runner for route-customer-symptom."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from domain_knowledge import route_customer_symptom  # noqa: E402
from runner_support import load_fixture, print_error, write_output  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run n1-support-agent/route-customer-symptom")
    parser.add_argument("--text")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    try:
        fixture = load_fixture(args.fixture) if args.fixture else {}
        text = args.text or fixture.get("text") or fixture_text(fixture)
        payload = route_customer_symptom(text)
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render(payload)
        write_output(content, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def fixture_text(fixture: dict) -> str:
    work_item = fixture.get("work_item") or fixture.get("card") or {}
    comments = fixture.get("comments") or {}
    comment_items = comments.get("comments", []) if isinstance(comments, dict) else comments or []
    return "\n".join(
        [
            str(work_item.get("title") or ""),
            str(work_item.get("description") or ""),
            *[str(item.get("text") or item.get("body") or "") for item in comment_items],
        ]
    )


def render(payload: dict) -> str:
    lines = [
        "# N1 Customer Symptom Route",
        "",
        f"- Route: {payload.get('routeId')}",
        f"- Domain: {payload.get('domain')}",
        f"- Confidence: {payload.get('confidence')}",
        f"- Matched aliases: {', '.join(payload.get('matchedAliases') or []) or '-'}",
        "",
        "## Minimum Checks",
        "",
    ]
    lines.extend(f"- {item}" for item in payload.get("minimumChecks") or [])
    lines.extend(["", "## Business Rules", ""])
    for rule in payload.get("businessRules") or []:
        lines.append(f"- {rule.get('id')}: {rule.get('supportImpact') or rule.get('rule')}")
    lines.extend(["", "## Contract", "", "```json", json.dumps(payload, ensure_ascii=False, indent=2), "```"])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
