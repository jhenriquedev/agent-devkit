#!/usr/bin/env python3
"""Runner for update-azure-card."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    DEFAULT_ANALYSIS_TAG,
    plan_or_apply_azure_actions,
    print_error,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run n1-support-agent/update-azure-card")
    parser.add_argument("--project", required=True)
    parser.add_argument("--card", type=int, required=True)
    parser.add_argument("--tag", default=DEFAULT_ANALYSIS_TAG)
    parser.add_argument("--target-state")
    parser.add_argument("--target-column")
    parser.add_argument("--current-state")
    parser.add_argument("--reason")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    try:
        actions = plan_or_apply_azure_actions(
            project=args.project,
            card_id=args.card,
            tag=args.tag,
            target_state=args.target_state,
            target_column=args.target_column,
            current_state=args.current_state,
            reason=args.reason,
            execute=args.execute,
            fixture=args.fixture,
        )
        payload = {
            "capability": "update-azure-card",
            "status": "completed",
            "mode": "executed" if args.execute else "dry_run",
            "azureActions": actions,
        }
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render(payload)
        write_output(content, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(payload: dict) -> str:
    lines = ["# N1 Azure Card Update", "", f"- Mode: {payload.get('mode')}", "", "## Actions", ""]
    for action in payload.get("azureActions") or []:
        lines.append(f"- {action.get('id')}: {action.get('mode')} / {action.get('status')}")
    lines.extend(["", "## Contract", "", "```json", json.dumps(payload, ensure_ascii=False, indent=2), "```"])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
