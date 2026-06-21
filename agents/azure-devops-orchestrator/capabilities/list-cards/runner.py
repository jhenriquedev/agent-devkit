#!/usr/bin/env python3
"""End-to-end runner for the list-cards capability."""

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
    get_repository,
    load_fixture,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run azure-devops-orchestrator/list-cards")
    parser.add_argument("--project")
    parser.add_argument("--wiql")
    parser.add_argument("--state")
    parser.add_argument("--assigned-to")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        payload = load_payload(args)
        markdown = render_list(payload, args)
        write_output(markdown, args.output)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


def load_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.fixture:
        data = load_fixture(args.fixture)
        if "items" in data:
            return data
        if "cards" in data:
            return {"count": len(data["cards"]), "items": data["cards"], "wiql": data.get("wiql", "")}
        raise ValueError("fixture must contain 'items' or 'cards'")

    if not args.project:
        raise ValueError("--project is required when --fixture is not provided")

    repo = get_repository()
    return repo.list_work_items(
        project=args.project,
        wiql=args.wiql,
        state=args.state,
        assigned_to=args.assigned_to,
        tags=args.tag,
        limit=args.limit,
    )


def render_list(payload: dict[str, Any], args: argparse.Namespace) -> str:
    items = payload.get("items", []) or []
    lines = [
        "# Listed Cards",
        "",
        "## Filters",
        "",
        f"- Project: {value_or_dash(args.project or payload.get('project'))}",
        f"- WIQL: {value_or_dash(args.wiql or payload.get('wiql'))}",
        f"- State: {value_or_dash(args.state)}",
        f"- Assigned to: {value_or_dash(args.assigned_to)}",
        f"- Tags: {format_tags(args.tag)}",
        f"- Limit: {value_or_dash(args.limit)}",
        "",
        "## Results",
        "",
        "| ID | Type | Title | State | Assigned To | Tags |",
        "|---|---|---|---|---|---|",
    ]
    for item in items:
        lines.append(
            "| "
            + " | ".join(
                [
                    value_or_dash(item.get("id")),
                    value_or_dash(item.get("work_item_type")),
                    clean_text(item.get("title")) or "-",
                    value_or_dash(item.get("state")),
                    value_or_dash(item.get("assigned_to")),
                    format_tags(item.get("tags") or []),
                ]
            )
            + " |"
        )

    if not items:
        lines.append("| - | - | No card found | - | - | - |")

    observations = []
    if not items:
        observations.append("No result returned for the provided filters.")
    if payload.get("count") == args.limit and items:
        observations.append("The response reached the configured limit; more cards may exist.")
    observations.append("Use `read-card` to inspect a specific item.")

    lines.extend(["", "## Observations", ""])
    lines.extend(f"- {item}" for item in observations)
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
