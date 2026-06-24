#!/usr/bin/env python3
"""Runner for execute-n1-card-runbook."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys
from typing import Any

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    DEFAULT_ANALYSIS_TAG,
    build_contract,
    mask_cpf,
    plan_or_apply_azure_actions,
    print_error,
    read_azure_card,
    render_contract_markdown,
    run_bpo_proposal_check,
    run_restrictive_base_check,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run n1-support-agent/execute-n1-card-runbook")
    parser.add_argument("--project", required=True)
    parser.add_argument("--card", type=int, required=True)
    parser.add_argument("--analysis-tag", default=DEFAULT_ANALYSIS_TAG)
    parser.add_argument("--target-state")
    parser.add_argument("--target-column")
    parser.add_argument("--reason")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    try:
        card_markdown, card = read_azure_card(args.project, args.card, fixture=args.fixture)
        restrictive_check = run_restrictive_base_check(card_markdown, fixture=args.fixture)
        bpo_check = run_bpo_proposal_check(card_markdown, fixture=args.fixture)
        azure_actions = plan_or_apply_azure_actions(
            project=args.project,
            card_id=args.card,
            tag=args.analysis_tag,
            target_state=args.target_state,
            target_column=args.target_column,
            current_state=card.get("state"),
            reason=args.reason,
            execute=args.execute,
            fixture=args.fixture,
        )
        contract = build_contract(
            project=args.project,
            card_id=args.card,
            card=card,
            card_markdown=card_markdown,
            azure_actions=azure_actions,
            execute=args.execute,
            tag=args.analysis_tag,
            target_column=args.target_column,
            restrictive_check=restrictive_check,
            bpo_check=bpo_check,
        )
        if args.format == "json":
            content = json.dumps(redact_contract_for_json(contract), ensure_ascii=False, indent=2) + "\n"
        else:
            content = render_contract_markdown(contract, card_markdown)
        write_output(content, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def redact_contract_for_json(value: Any, key: str = "") -> Any:
    if isinstance(value, dict):
        return {item_key: redact_contract_for_json(item_value, item_key) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [redact_contract_for_json(item, key) for item in value]
    if is_secret_key(key):
        return "***REDACTED***" if value is not None else None
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value


def is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(
        term in lowered
        for term in (
            "password",
            "passwd",
            "senha",
            "secret",
            "token",
            "api_key",
            "apikey",
            "pat",
            "connection_string",
        )
    )


def redact_sensitive_text(value: str) -> str:
    text = re.sub(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", lambda match: mask_cpf(match.group(0)), value)
    return re.sub(
        r"(?i)\b(token|secret|api[_-]?key|password|pat|connection_string)\s*[:=]\s*[^\s,;]+",
        lambda match: f"{match.group(1)}=***REDACTED***",
        text,
    )


if __name__ == "__main__":
    raise SystemExit(main())
