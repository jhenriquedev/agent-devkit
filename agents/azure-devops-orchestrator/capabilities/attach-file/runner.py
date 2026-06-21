#!/usr/bin/env python3
"""End-to-end runner for the attach-file capability."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import load_work_item_only, render_write_result, value_or_dash, write_output  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run azure-devops-orchestrator/attach-file")
    parser.add_argument("--id", type=int, dest="work_item_id")
    parser.add_argument("--project")
    parser.add_argument("--file", required=True)
    parser.add_argument("--comment")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        file_path = Path(args.file).expanduser()
        if not file_path.exists():
            raise ValueError(f"file not found: {file_path}")
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
        result = execute_or_preview(args, repo, work_item_id, str(file_path))
        markdown = render_plan(work_item, args, result, str(file_path))
        write_output(markdown, args.output)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


def execute_or_preview(
    args: argparse.Namespace,
    repo: Any | None,
    work_item_id: int,
    file_path: str,
) -> dict[str, Any]:
    if args.fixture:
        return {
            "dry_run": not args.execute,
            "work_item_id": work_item_id,
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "operation": "attach_file",
            "fixture_mode": True,
        }
    if repo is None:
        raise ValueError("repository unavailable")
    return repo.attach_file(
        work_item_id,
        file_path,
        project=args.project,
        comment=args.comment,
        dry_run=not args.execute,
    )


def render_plan(
    work_item: dict[str, Any],
    args: argparse.Namespace,
    result: dict[str, Any],
    file_path: str,
) -> str:
    lines = [
        "# Card Attachment",
        "",
        "## Target",
        "",
        f"- Card: {value_or_dash(work_item.get('id'))}",
        f"- Title: {value_or_dash(work_item.get('title'))}",
        "",
        "## File",
        "",
        f"- Path: {value_or_dash(file_path)}",
        f"- Name: {value_or_dash(Path(file_path).name)}",
        f"- Comment: {value_or_dash(args.comment)}",
        "",
        "## Result",
        "",
        f"- Status: {'executed' if args.execute else 'planned'}",
        *render_write_result(result),
    ]
    if result.get("attachment_url"):
        lines.append(f"- Attachment URL: {value_or_dash(result.get('attachment_url'))}")
    if not args.execute:
        lines.extend(["", "## Confirmation", "", "- Re-run with `--execute` to attach."])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
