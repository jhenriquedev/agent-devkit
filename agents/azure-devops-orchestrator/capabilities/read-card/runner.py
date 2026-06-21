#!/usr/bin/env python3
"""End-to-end runner for the read-card capability."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CAPABILITY_DIR = Path(__file__).resolve().parent
AGENT_DIR = CAPABILITY_DIR.parents[1]
AZURE_DIR = AGENT_DIR / "infra" / "integrations" / "azure"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run azure-devops-orchestrator/read-card")
    parser.add_argument("--id", type=int, dest="work_item_id")
    parser.add_argument("--project")
    parser.add_argument("--include-comments", action="store_true")
    parser.add_argument("--fixture", help="read work item data from a JSON fixture")
    parser.add_argument("--output", help="write Markdown output to this file")
    args = parser.parse_args()

    try:
        payload = load_payload(args)
        markdown = render_analysis(
            payload["work_item"],
            payload.get("comments") if args.include_comments else None,
        )
        if args.output:
            Path(args.output).write_text(markdown, encoding="utf-8")
        else:
            print(markdown)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


def load_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.fixture:
        data = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        if "work_item" not in data:
            raise ValueError("fixture must contain 'work_item'")
        return data

    if not args.work_item_id:
        raise ValueError("--id is required when --fixture is not provided")

    sys.path.insert(0, str(AZURE_DIR))
    from azure_repository import AzureRepository  # pylint: disable=import-error

    repo = AzureRepository()
    work_item = repo.get_work_item(
        args.work_item_id,
        project=args.project,
        expand_relations=True,
    )
    payload: dict[str, Any] = {"work_item": work_item}
    if args.include_comments:
        payload["comments"] = repo.get_work_item_comments(
            args.work_item_id,
            project=args.project,
        )
    return payload


def render_analysis(work_item: dict[str, Any], comments: dict[str, Any] | None = None) -> str:
    tags = work_item.get("tags") or []
    comments_list = (comments or {}).get("comments", [])
    acceptance_criteria = clean_text(work_item.get("acceptance_criteria"))
    description = clean_text(work_item.get("description"))
    attachments = get_attachments(work_item)

    lines = [
        "# Card Analysis",
        "",
        "## Identification",
        "",
        f"- ID: {value_or_dash(work_item.get('id'))}",
        f"- Type: {value_or_dash(work_item.get('work_item_type'))}",
        f"- Title: {value_or_dash(work_item.get('title'))}",
        f"- State: {value_or_dash(work_item.get('state'))}",
        f"- Current column: {value_or_dash(work_item.get('board_column'))}",
        f"- Created at: {value_or_dash(work_item.get('created_date'))}",
        f"- Changed at: {value_or_dash(work_item.get('changed_date'))}",
        f"- Assigned to: {value_or_dash(work_item.get('assigned_to'))}",
        f"- Tags: {', '.join(tags) if tags else '-'}",
        "",
        "## Collected Facts",
        "",
        f"- Card found in Azure DevOps with state `{value_or_dash(work_item.get('state'))}`.",
        f"- Description: {description or '-'}",
        f"- URL: {value_or_dash(work_item.get('url'))}",
        "",
        "## Attachments",
        "",
        *render_attachments(attachments),
        "",
        "## Acceptance Criteria And Scope",
        "",
        f"- {acceptance_criteria if acceptance_criteria else 'Acceptance criteria are missing.'}",
        "",
        "## Relevant Comments",
        "",
    ]

    if comments_list:
        for comment in comments_list:
            author = value_or_dash(comment.get("author"))
            created_at = value_or_dash(comment.get("created_at"))
            text = clean_text(comment.get("text")) or "-"
            lines.append(f"- {created_at} - {author}: {text}")
    else:
        lines.append("- No comments loaded.")

    gaps = identify_gaps(work_item, comments_list)
    lines.extend(
        [
            "",
            "## Gaps And Risks",
            "",
            *[f"- {item}" for item in gaps],
            "",
            "## Inferences",
            "",
            "- Keep collected facts separate from inferences.",
            "- Validate gaps with the card owner before executing changes.",
            "",
            "## Recommended Next Steps",
            "",
            "- Confirm acceptance criteria when they are missing or incomplete.",
            "- Review recent comments before planning implementation.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def identify_gaps(work_item: dict[str, Any], comments: list[dict[str, Any]]) -> list[str]:
    gaps = []
    if not clean_text(work_item.get("acceptance_criteria")):
        gaps.append("Acceptance criteria are missing.")
    if not clean_text(work_item.get("description")):
        gaps.append("Description is missing or empty.")
    if not work_item.get("assigned_to"):
        gaps.append("Assignee is not defined.")
    if comments and any("falta" in clean_text(item.get("text")).lower() for item in comments):
        gaps.append("Comments indicate pending items that need refinement.")
    return gaps or ["No clear gap found in the loaded data."]


def get_attachments(work_item: dict[str, Any]) -> list[dict[str, Any]]:
    relations = work_item.get("relations") or []
    return [item for item in relations if item.get("rel") == "AttachedFile"]


def render_attachments(attachments: list[dict[str, Any]]) -> list[str]:
    if not attachments:
        return ["- No attachments found."]

    lines = []
    for attachment in attachments:
        attributes = attachment.get("attributes") or {}
        name = value_or_dash(attributes.get("name"))
        comment = clean_text(attributes.get("comment"))
        suffix = f" - {comment}" if comment else ""
        lines.append(f"- {name}{suffix}")
    return lines


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split())


def value_or_dash(value: Any) -> str:
    text = clean_text(value)
    return text if text else "-"


if __name__ == "__main__":
    raise SystemExit(main())
