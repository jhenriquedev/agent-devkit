#!/usr/bin/env python3
"""End-to-end runner for the assign-card capability."""

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
    load_fixture,
    load_work_item_only,
    render_write_result,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run azure-devops-orchestrator/assign-card")
    parser.add_argument("--id", type=int, dest="work_item_id")
    parser.add_argument("--project")
    parser.add_argument("--assignee", required=True)
    parser.add_argument("--reason")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--skip-identity-lookup", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        if not args.work_item_id and not args.fixture:
            raise ValueError("--id is required when --fixture is not provided")
        work_item_id = args.work_item_id or 0
        work_item, repo = load_work_item_only(
            fixture=args.fixture,
            project=args.project,
            work_item_id=work_item_id,
        )
        if args.fixture:
            work_item_id = int(work_item.get("id") or work_item_id)
        users = load_users(args, repo)
        target = resolve_assignee(args.assignee, users, args.skip_identity_lookup)
        plan = build_plan(work_item, target)
        result = execute_plan(args, repo, work_item_id, plan)
        markdown = render_plan(work_item, users, target, plan, result, args)
        write_output(markdown, args.output)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


def load_users(args: argparse.Namespace, repo: Any | None) -> list[dict[str, Any]]:
    if args.skip_identity_lookup:
        return []
    if args.fixture:
        return load_fixture(args.fixture).get("users", [])
    if repo is None:
        raise ValueError("repository unavailable")
    return repo.find_users(args.assignee, project=args.project).get("users", [])


def resolve_assignee(
    assignee: str,
    users: list[dict[str, Any]],
    skip_identity_lookup: bool,
) -> dict[str, Any]:
    if skip_identity_lookup:
        return {"unique_name": assignee, "display_name": assignee, "source": "input"}
    if not users:
        raise ValueError(f"no Azure DevOps identity found for assignee: {assignee}")

    lowered = assignee.lower()
    exact = [
        user
        for user in users
        if lowered
        in {
            str(user.get("unique_name") or "").lower(),
            str(user.get("email") or "").lower(),
            str(user.get("display_name") or "").lower(),
        }
    ]
    if len(exact) == 1:
        return exact[0]
    if len(users) == 1:
        return users[0]
    raise ValueError("multiple identity candidates found; refine --assignee")


def build_plan(work_item: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    current = work_item.get("assigned_to")
    target_value = target.get("unique_name") or target.get("email") or target.get("display_name")
    changed = str(current or "").lower() != str(target_value or "").lower()
    operations = []
    if changed:
        operations.append(json_patch_replace("/fields/System.AssignedTo", target_value))
    return {
        "current_assignee": current,
        "target_assignee": target_value,
        "changed": changed,
        "operations": operations,
    }


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
    users: list[dict[str, Any]],
    target: dict[str, Any],
    plan: dict[str, Any],
    result: dict[str, Any],
    args: argparse.Namespace,
) -> str:
    lines = [
        "# Card Assignment",
        "",
        "## Target",
        "",
        f"- Card: {value_or_dash(work_item.get('id'))}",
        f"- Title: {value_or_dash(work_item.get('title'))}",
        "",
        "## Identity",
        "",
        f"- Candidates found: {len(users) if not args.skip_identity_lookup else 'lookup skipped'}",
        f"- Current assignee: {value_or_dash(plan['current_assignee'])}",
        f"- Target assignee: {value_or_dash(plan['target_assignee'])}",
        f"- Has change: {value_or_dash(plan['changed'])}",
        f"- Target name: {value_or_dash(target.get('display_name'))}",
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
