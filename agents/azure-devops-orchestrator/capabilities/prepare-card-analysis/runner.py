#!/usr/bin/env python3
"""End-to-end runner for the prepare-card-analysis capability."""

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
    format_tags,
    get_attachments,
    load_work_item_payload,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run azure-devops-orchestrator/prepare-card-analysis"
    )
    parser.add_argument("--id", type=int, dest="work_item_id")
    parser.add_argument("--project")
    parser.add_argument("--analysis-type", default="support")
    parser.add_argument("--include-comment-draft", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        if not args.work_item_id and not args.fixture:
            raise ValueError("--id is required when --fixture is not provided")
        payload = load_work_item_payload(
            fixture=args.fixture,
            project=args.project,
            work_item_id=args.work_item_id or 0,
            include_comments=True,
        )
        markdown = render_analysis(payload, args)
        write_output(markdown, args.output)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


def render_analysis(payload: dict[str, Any], args: argparse.Namespace) -> str:
    work_item = payload["work_item"]
    comments = (payload.get("comments") or {}).get("comments", [])
    demand_type = classify_demand(work_item)
    gaps = identify_gaps(work_item, comments)
    hypotheses = build_hypotheses(work_item, demand_type)
    next_steps = build_next_steps(work_item, gaps, demand_type)

    lines = [
        "# Card Operational Analysis",
        "",
        "## Summary",
        "",
        f"- Card: {value_or_dash(work_item.get('id'))}",
        f"- Title: {value_or_dash(work_item.get('title'))}",
        f"- Identified type: {demand_type}",
        f"- Current status: {value_or_dash(work_item.get('state'))}",
        f"- Current column: {value_or_dash(work_item.get('board_column'))}",
        f"- Assigned to: {value_or_dash(work_item.get('assigned_to'))}",
        f"- Tags: {format_tags(work_item.get('tags') or [])}",
        "",
        "## Collected Facts",
        "",
        f"- Work item type: {value_or_dash(work_item.get('work_item_type'))}",
        f"- Created at: {value_or_dash(work_item.get('created_date'))}",
        f"- Changed at: {value_or_dash(work_item.get('changed_date'))}",
        f"- Loaded comments: {len(comments)}",
        f"- Loaded attachments: {len(get_attachments(work_item))}",
        "",
        "## Evidence",
        "",
        f"- Description: {summarize_description(work_item.get('description'))}",
        "",
        "## Hypotheses",
        "",
        *[f"- {item}" for item in hypotheses],
        "",
        "## Gaps",
        "",
        *[f"- {item}" for item in gaps],
        "",
        "## Next Steps",
        "",
        *[f"- {item}" for item in next_steps],
    ]
    if args.include_comment_draft:
        lines.extend(["", "## Suggested Comment", "", "```text", build_comment_draft(work_item, gaps), "```"])
        lines.extend(["", "Publishing: use `comment-card` to publish after review."])
    lines.extend(["", "## Write Operations", "", "- No write operation was executed."])
    return "\n".join(lines).rstrip() + "\n"


def classify_demand(work_item: dict[str, Any]) -> str:
    text = " ".join(
        [
            clean_text(work_item.get("title")),
            clean_text(work_item.get("description")),
            " ".join(work_item.get("tags") or []),
        ]
    ).lower()
    if any(term in text for term in ["warning", "erro", "error", "exception", "bugfix"]):
        return "bug/incident"
    if any(term in text for term in ["suporte", "sustentacao", "monitoramento"]):
        return "support"
    if any(term in text for term in ["melhoria", "feature"]):
        return "improvement"
    return "triage"


def identify_gaps(work_item: dict[str, Any], comments: list[dict[str, Any]]) -> list[str]:
    gaps = []
    if not clean_text(work_item.get("acceptance_criteria")):
        gaps.append("Acceptance criteria are missing.")
    if not clean_text(work_item.get("description")):
        gaps.append("Description is missing or empty.")
    if not work_item.get("assigned_to"):
        gaps.append("Assignee is not defined.")
    if not comments:
        gaps.append("No comments loaded.")
    return gaps or ["No clear gap found in the loaded data."]


def build_hypotheses(work_item: dict[str, Any], demand_type: str) -> list[str]:
    description = clean_text(work_item.get("description")).lower()
    hypotheses = []
    if "elastic beanstalk" in description or "health" in description:
        hypotheses.append("There may be degradation or a recent event in the Elastic Beanstalk environment.")
    if "cloudwatch" in description or "log group" in description:
        hypotheses.append("Operational log evidence must be validated before concluding a root cause.")
    if demand_type == "bug/incident":
        hypotheses.append("Treat this demand as an investigation until evidence confirms a fix.")
    return hypotheses or ["No strong technical hypothesis is available from the loaded data only."]


def build_next_steps(
    work_item: dict[str, Any],
    gaps: list[str],
    demand_type: str,
) -> list[str]:
    steps = ["Validate card facts before executing any write operation."]
    if "Assignee is not defined." in gaps:
        steps.append("Set the assignee with `assign-card` when ownership is clear.")
    if "Acceptance criteria are missing." in gaps:
        steps.append("Request or record acceptance criteria before closing the card.")
    if demand_type == "bug/incident":
        steps.append("Collect operational evidence and confirm impact before moving status.")
    if work_item.get("state"):
        steps.append("Use `move-card` only after validating the target state and reason.")
    return steps


def summarize_description(description: Any) -> str:
    text = clean_text(description)
    if not text:
        return "-"
    return text[:900] + ("..." if len(text) > 900 else "")


def build_comment_draft(work_item: dict[str, Any], gaps: list[str]) -> str:
    title = value_or_dash(work_item.get("title"))
    gap_text = "; ".join(gaps)
    return (
        f"Initial analysis for card `{title}` completed. "
        f"Identified gaps: {gap_text}. "
        "Recommended next step: validate evidence and define routing before changing status."
    )


if __name__ == "__main__":
    raise SystemExit(main())
