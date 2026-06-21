#!/usr/bin/env python3
"""End-to-end runner for the comment-card capability."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    clean_text,
    load_work_item_only,
    render_write_result,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run azure-devops-orchestrator/comment-card")
    parser.add_argument("--id", type=int, dest="work_item_id")
    parser.add_argument("--project")
    parser.add_argument("--comment")
    parser.add_argument("--comment-intent")
    parser.add_argument("--tone", default="professional")
    parser.add_argument("--include-context-summary", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        if not args.work_item_id and not args.fixture:
            raise ValueError("--id is required when --fixture is not provided")
        comment = build_comment(args)
        work_item_id = args.work_item_id or 0
        work_item, repo = load_work_item_only(
            fixture=args.fixture,
            project=args.project,
            work_item_id=work_item_id,
        )
        if args.fixture:
            work_item_id = int(work_item.get("id") or work_item_id)
        result = execute_or_preview(args, repo, work_item_id, comment)
        markdown = render_comment_plan(work_item, comment, args, result)
        write_output(markdown, args.output)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


def build_comment(args: argparse.Namespace) -> str:
    comment = clean_text(args.comment)
    if not comment and args.comment_intent:
        comment = f"Record: {clean_text(args.comment_intent)}"
    if not comment:
        raise ValueError("--comment or --comment-intent is required")
    return comment


def execute_or_preview(
    args: argparse.Namespace,
    repo: Any | None,
    work_item_id: int,
    comment: str,
) -> dict[str, Any]:
    if args.fixture:
        return {
            "dry_run": not args.execute,
            "work_item_id": work_item_id,
            "comment": comment,
            "operation": "add_comment",
            "fixture_mode": True,
        }
    if repo is None:
        raise ValueError("repository unavailable")
    return repo.add_comment(
        work_item_id,
        comment,
        project=args.project,
        dry_run=not args.execute,
    )


def classify_risk(comment: str) -> tuple[str, str]:
    lowered = comment.lower()
    high_terms = ["senha", "token", "cpf", "segredo", "credencial", "producao"]
    medium_terms = ["prazo", "comprometo", "assumir", "responsavel", "deploy", "corrigido"]
    if any(term in lowered for term in high_terms):
        return "high", "Comment may include sensitive data or critical environment details."
    if any(term in lowered for term in medium_terms):
        return "medium", "Comment may record a commitment, deadline, or operational action."
    return "low", "Informational comment with no clear operational commitment."


def render_comment_plan(
    work_item: dict[str, Any],
    comment: str,
    args: argparse.Namespace,
    result: dict[str, Any],
) -> str:
    risk, reason = classify_risk(comment)
    status = "executed" if args.execute else "planned"
    lines = [
        "# Card Comment",
        "",
        "## Target",
        "",
        f"- Card: {value_or_dash(work_item.get('id'))}",
        f"- Title: {value_or_dash(work_item.get('title'))}",
        f"- Current state: {value_or_dash(work_item.get('state'))}",
        "",
        "## Comment",
        "",
        "```text",
        comment,
        "```",
        "",
        "## Risk",
        "",
        f"- Level: {risk}",
        f"- Reason: {reason}",
        "",
        "## Result",
        "",
        f"- Status: {status}",
        *render_write_result(result),
    ]
    if not args.execute:
        lines.extend(["", "## Confirmation", "", "- Re-run with `--execute` to publish."])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
