#!/usr/bin/env python3
"""End-to-end runner for the move-card capability."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    json_patch_replace,
    load_work_item_only,
    render_write_result,
    value_or_dash,
    write_output,
)


CLOSING_STATES = {"done", "closed", "resolved", "removed"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run azure-devops-orchestrator/move-card")
    parser.add_argument("--id", type=int, dest="work_item_id")
    parser.add_argument("--project")
    parser.add_argument("--state", required=True)
    parser.add_argument("--board-column")
    parser.add_argument("--reason")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        if not args.work_item_id and not args.fixture:
            raise ValueError("--id is required when --fixture is not provided")
        if args.state.lower() in CLOSING_STATES and not args.reason:
            raise ValueError("closing states require --reason")
        work_item_id = args.work_item_id or 0
        work_item, repo = load_work_item_only(
            fixture=args.fixture,
            project=args.project,
            work_item_id=work_item_id,
        )
        if args.fixture:
            work_item_id = int(work_item.get("id") or work_item_id)
        plan = build_plan(work_item, args)
        result = execute_plan(args, repo, work_item_id, plan)
        markdown = render_plan(work_item, plan, result, args)
        write_output(markdown, args.output)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


def build_plan(work_item: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    operations = []
    if str(work_item.get("state") or "").lower() != args.state.lower():
        operations.append(json_patch_replace("/fields/System.State", args.state))
    if args.board_column and str(work_item.get("board_column") or "").lower() != args.board_column.lower():
        operations.append(json_patch_replace("/fields/System.BoardColumn", args.board_column))
    risk = classify_risk(args.state)
    return {
        "current_state": work_item.get("state"),
        "target_state": args.state,
        "current_column": work_item.get("board_column"),
        "target_column": args.board_column,
        "risk": risk,
        "changed": bool(operations),
        "operations": operations,
    }


def classify_risk(state: str) -> str:
    lowered = state.lower()
    if lowered in CLOSING_STATES:
        return "high"
    if lowered in {"active", "doing", "in progress", "committed"}:
        return "medium"
    return "low"


def execute_plan(
    args: argparse.Namespace,
    repo: Any | None,
    work_item_id: int,
    plan: dict[str, Any],
) -> dict[str, Any]:
    if not plan["changed"]:
        return {"dry_run": True, "work_item_id": work_item_id, "operations": [], "no_op": True}
    if args.fixture:
        return {
            "dry_run": not args.execute,
            "work_item_id": work_item_id,
            "operations": plan["operations"],
            "fixture_mode": True,
        }
    if repo is None:
        raise ValueError("repository unavailable")
    return repo.update_work_item(
        work_item_id,
        plan["operations"],
        project=args.project,
        dry_run=not args.execute,
        reason=args.reason,
    )


def render_plan(
    work_item: dict[str, Any],
    plan: dict[str, Any],
    result: dict[str, Any],
    args: argparse.Namespace,
) -> str:
    lines = [
        "# Card Move",
        "",
        "## Target",
        "",
        f"- Card: {value_or_dash(work_item.get('id'))}",
        f"- Title: {value_or_dash(work_item.get('title'))}",
        "",
        "## Before And After",
        "",
        f"- Current state: {value_or_dash(plan['current_state'])}",
        f"- Target state: {value_or_dash(plan['target_state'])}",
        f"- Current column: {value_or_dash(plan['current_column'])}",
        f"- Target column: {value_or_dash(plan['target_column'])}",
        f"- Risk: {plan['risk']}",
        f"- Has change: {value_or_dash(plan['changed'])}",
        "",
        "## Result",
        "",
        f"- Status: {'executed' if args.execute and plan['changed'] else 'planned'}",
        *render_write_result(result),
    ]
    if not args.execute and plan["changed"]:
        lines.extend(["", "## Confirmation", "", "- Re-run with `--execute` to apply."])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
