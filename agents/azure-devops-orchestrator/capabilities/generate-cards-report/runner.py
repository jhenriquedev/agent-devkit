#!/usr/bin/env python3
"""End-to-end runner for the generate-cards-report capability."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    clean_text,
    format_tags,
    get_attachments,
    get_repository,
    load_fixture,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run azure-devops-orchestrator/generate-cards-report"
    )
    parser.add_argument("--project")
    parser.add_argument("--wiql")
    parser.add_argument("--state")
    parser.add_argument("--assigned-to")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--include-comments", action="store_true")
    parser.add_argument("--include-details", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        payload = load_report_payload(args)
        markdown = render_report(payload, args)
        write_output(markdown, args.output)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


def load_report_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.fixture:
        data = load_fixture(args.fixture)
        if "cards" not in data:
            raise ValueError("fixture must contain 'cards'")
        return {
            "project": data.get("project") or args.project,
            "wiql": data.get("wiql", ""),
            "cards": data.get("cards") or [],
            "limit": data.get("limit", args.limit),
            "list_count": data.get("list_count", len(data.get("cards") or [])),
            "filters": data.get("filters", {}),
        }

    if not args.project:
        raise ValueError("--project is required when --fixture is not provided")

    repo = get_repository()
    listing = repo.list_work_items(
        project=args.project,
        wiql=args.wiql,
        state=args.state,
        assigned_to=args.assigned_to,
        tags=args.tag,
        limit=args.limit,
    )
    cards = []
    for item in listing.get("items", []) or []:
        work_item_id = item.get("id")
        if work_item_id is None:
            continue
        card: dict[str, Any] = {
            "work_item": repo.get_work_item(
                int(work_item_id),
                project=args.project,
                expand_relations=True,
            )
        }
        if args.include_comments:
            card["comments"] = repo.get_work_item_comments(int(work_item_id), project=args.project)
        cards.append(card)

    return {
        "project": args.project,
        "wiql": listing.get("wiql", ""),
        "cards": cards,
        "limit": args.limit,
        "list_count": listing.get("count", len(cards)),
        "filters": {
            "state": args.state,
            "assigned_to": args.assigned_to,
            "tags": args.tag,
        },
    }


def render_report(payload: dict[str, Any], args: argparse.Namespace) -> str:
    cards = normalize_cards(payload.get("cards") or [])
    summary = build_summary(cards)
    filters = payload.get("filters") or {}
    limit = int(payload.get("limit") or args.limit)
    hit_limit = len(cards) >= limit and bool(cards)

    lines = [
        "# Azure DevOps Cards Report",
        "",
        "## Query",
        "",
        f"- Project: {value_or_dash(payload.get('project') or args.project)}",
        f"- WIQL: {value_or_dash(args.wiql or payload.get('wiql'))}",
        f"- State: {value_or_dash(args.state or filters.get('state'))}",
        f"- Assigned to: {value_or_dash(args.assigned_to or filters.get('assigned_to'))}",
        f"- Tags: {format_tags(args.tag or filters.get('tags') or [])}",
        f"- Limit: {limit}",
        f"- Comments included: {value_or_dash(args.include_comments)}",
        f"- Details included: {value_or_dash(args.include_details)}",
        "",
        "## Executive Summary",
        "",
        f"- Total de cards: {summary['total']}",
        f"- Without assignee: {len(summary['without_assignee'])}",
        f"- Without acceptance criteria: {len(summary['without_acceptance_criteria'])}",
        f"- Without description: {len(summary['without_description'])}",
        f"- With attachments: {len(summary['with_attachments'])}",
        f"- With comments: {len(summary['with_comments'])}",
        f"- Query reached limit: {value_or_dash(hit_limit)}",
        "",
        "### By State",
        "",
        *render_counter(summary["by_state"]),
        "",
        "### By Assignee",
        "",
        *render_counter(summary["by_assignee"]),
        "",
        "## Consolidated Table",
        "",
        "| ID | Type | Title | State | Column | Assigned To | Tags | Comments | Attachments |",
        "|---|---|---|---|---|---|---|---|---|",
        *render_table_rows(cards),
        "",
        "## Operational Gaps",
        "",
        *render_gaps(summary),
    ]
    if hit_limit:
        lines.extend(["", "## Warnings", "", "- The response reached the configured limit; more cards may exist."])
    if args.include_details:
        lines.extend(["", "## Details By Card", ""])
        for card in cards:
            lines.extend(render_card_detail(card))
    lines.extend(["", "## Write Operations", "", "- No write operation was executed."])
    return "\n".join(lines).rstrip() + "\n"


def normalize_cards(raw_cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards = []
    for raw in raw_cards:
        if "work_item" in raw:
            work_item = raw.get("work_item") or {}
            comments = raw.get("comments") or {}
        else:
            work_item = raw
            comments = raw.get("comments") or {}
        comment_list = comments.get("comments", comments if isinstance(comments, list) else [])
        cards.append({"work_item": work_item, "comments": comment_list or []})
    return cards


def build_summary(cards: list[dict[str, Any]]) -> dict[str, Any]:
    by_state: Counter[str] = Counter()
    by_assignee: Counter[str] = Counter()
    without_assignee = []
    without_acceptance_criteria = []
    without_description = []
    with_attachments = []
    with_comments = []
    for card in cards:
        work_item = card["work_item"]
        work_item_id = work_item.get("id")
        by_state[value_or_dash(work_item.get("state"))] += 1
        by_assignee[value_or_dash(work_item.get("assigned_to"))] += 1
        if not work_item.get("assigned_to"):
            without_assignee.append(work_item_id)
        if not clean_text(work_item.get("acceptance_criteria")):
            without_acceptance_criteria.append(work_item_id)
        if not clean_text(work_item.get("description")):
            without_description.append(work_item_id)
        if get_attachments(work_item):
            with_attachments.append(work_item_id)
        if card.get("comments"):
            with_comments.append(work_item_id)
    return {
        "total": len(cards),
        "by_state": by_state,
        "by_assignee": by_assignee,
        "without_assignee": without_assignee,
        "without_acceptance_criteria": without_acceptance_criteria,
        "without_description": without_description,
        "with_attachments": with_attachments,
        "with_comments": with_comments,
    }


def render_counter(counter: Counter[str]) -> list[str]:
    if not counter:
        return ["- No item."]
    return [f"- {key}: {count}" for key, count in sorted(counter.items())]


def render_table_rows(cards: list[dict[str, Any]]) -> list[str]:
    if not cards:
        return ["| - | - | No card found | - | - | - | - | - | - |"]
    rows = []
    for card in cards:
        work_item = card["work_item"]
        rows.append(
            "| "
            + " | ".join(
                [
                    value_or_dash(work_item.get("id")),
                    value_or_dash(work_item.get("work_item_type")),
                    clean_text(work_item.get("title")) or "-",
                    value_or_dash(work_item.get("state")),
                    value_or_dash(work_item.get("board_column")),
                    value_or_dash(work_item.get("assigned_to")),
                    format_tags(work_item.get("tags") or []),
                    str(len(card.get("comments") or [])),
                    str(len(get_attachments(work_item))),
                ]
            )
            + " |"
        )
    return rows


def render_gaps(summary: dict[str, Any]) -> list[str]:
    return [
        f"- Cards without assignee: {format_ids(summary['without_assignee'])}",
        f"- Cards without acceptance criteria: {format_ids(summary['without_acceptance_criteria'])}",
        f"- Cards without description: {format_ids(summary['without_description'])}",
    ]


def render_card_detail(card: dict[str, Any]) -> list[str]:
    work_item = card["work_item"]
    comments = card.get("comments") or []
    attachments = get_attachments(work_item)
    return [
        f"### Card {value_or_dash(work_item.get('id'))} - {value_or_dash(work_item.get('title'))}",
        "",
        f"- Type: {value_or_dash(work_item.get('work_item_type'))}",
        f"- State: {value_or_dash(work_item.get('state'))}",
        f"- Column: {value_or_dash(work_item.get('board_column'))}",
        f"- Created at: {value_or_dash(work_item.get('created_date'))}",
        f"- Changed at: {value_or_dash(work_item.get('changed_date'))}",
        f"- Assigned to: {value_or_dash(work_item.get('assigned_to'))}",
        f"- Tags: {format_tags(work_item.get('tags') or [])}",
        f"- Comments: {len(comments)}",
        f"- Attachments: {len(attachments)}",
        f"- URL: {value_or_dash(work_item.get('url'))}",
        "",
        f"Summary: {summarize(work_item.get('description'))}",
        "",
    ]


def summarize(value: Any, limit: int = 500) -> str:
    text = clean_text(value)
    if not text:
        return "-"
    return text[:limit] + ("..." if len(text) > limit else "")


def format_ids(values: list[Any]) -> str:
    valid = [str(value) for value in values if value is not None]
    return ", ".join(valid) if valid else "-"


if __name__ == "__main__":
    raise SystemExit(main())
