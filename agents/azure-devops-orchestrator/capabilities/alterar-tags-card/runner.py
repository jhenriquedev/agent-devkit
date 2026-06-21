#!/usr/bin/env python3
"""End-to-end runner for the alterar-tags-card capability."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    format_tags,
    json_patch_replace,
    load_work_item_only,
    normalize_tags,
    parse_tags,
    render_write_result,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run azure-devops-orchestrator/alterar-tags-card")
    parser.add_argument("--id", type=int, dest="work_item_id")
    parser.add_argument("--project")
    parser.add_argument("--add-tag", action="append", default=[])
    parser.add_argument("--remove-tag", action="append", default=[])
    parser.add_argument("--reason")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        if not args.work_item_id and not args.fixture:
            raise ValueError("--id is required when --fixture is not provided")
        if not args.add_tag and not args.remove_tag:
            raise ValueError("at least one --add-tag or --remove-tag is required")
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
    current = normalize_tags(work_item.get("tags") or [])
    add_tags = normalize_tags(parse_tags(args.add_tag))
    remove_tags = normalize_tags(parse_tags(args.remove_tag))
    remove_keys = {tag.lower() for tag in remove_tags}
    final_tags = [tag for tag in current if tag.lower() not in remove_keys]
    final_tags = normalize_tags([*final_tags, *add_tags])
    changed = [tag.lower() for tag in current] != [tag.lower() for tag in final_tags]
    operations = []
    if changed:
        operations.append(json_patch_replace("/fields/System.Tags", "; ".join(final_tags)))
    return {
        "current_tags": current,
        "add_tags": add_tags,
        "remove_tags": remove_tags,
        "final_tags": final_tags,
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
    plan: dict[str, Any],
    result: dict[str, Any],
    args: argparse.Namespace,
) -> str:
    lines = [
        "# Alteracao de Tags do Card",
        "",
        "## Alvo",
        "",
        f"- Card: {value_or_dash(work_item.get('id'))}",
        f"- Titulo: {value_or_dash(work_item.get('title'))}",
        "",
        "## Diff",
        "",
        f"- Tags atuais: {format_tags(plan['current_tags'])}",
        f"- Adicionar: {format_tags(plan['add_tags'])}",
        f"- Remover: {format_tags(plan['remove_tags'])}",
        f"- Tags finais: {format_tags(plan['final_tags'])}",
        f"- Mudanca real: {value_or_dash(plan['changed'])}",
        "",
        "## Resultado",
        "",
        f"- Status: {'executado' if args.execute and plan['changed'] else 'planejado'}",
        *render_write_result(result),
    ]
    if not args.execute and plan["changed"]:
        lines.extend(["", "## Confirmacao", "", "- Reexecute com `--execute` para aplicar."])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
