#!/usr/bin/env python3
"""Generic runner for N1 auxiliary capabilities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def run(capability: str) -> int:
    parser = argparse.ArgumentParser(description=f"Run n1-support-agent/{capability}")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()
    payload = load_payload(capability, args.fixture)
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render(payload)
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        print(content)
    return 0


def load_payload(capability: str, fixture: str | None) -> dict[str, Any]:
    if fixture:
        return json.loads(Path(fixture).read_text(encoding="utf-8"))
    return {
        "capability": capability,
        "status": "contract_ready",
        "message": "This auxiliary N1 capability is represented as a contract and is orchestrated by execute-n1-card-runbook.",
    }


def render(payload: dict[str, Any]) -> str:
    lines = [f"# N1 {str(payload.get('capability', 'Capability')).replace('-', ' ').title()}", ""]
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            lines.extend([f"## {key}", "", "```json", json.dumps(value, ensure_ascii=False, indent=2), "```", ""])
        else:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines).rstrip() + "\n"
