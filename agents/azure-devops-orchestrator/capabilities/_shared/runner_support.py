#!/usr/bin/env python3
"""Shared helpers for Azure DevOps Orchestrator capability runners."""

from __future__ import annotations

import json
import re
import sys
from html import unescape
from pathlib import Path
from typing import Any


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
AZURE_DIR = AGENT_DIR / "infra" / "integrations" / "azure"


def load_fixture(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_repository() -> Any:
    sys.path.insert(0, str(AZURE_DIR))
    from azure_repository import AzureRepository  # pylint: disable=import-error

    return AzureRepository()


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(unescape(text).split())


def value_or_dash(value: Any) -> str:
    text = clean_text(value)
    return text if text else "-"


def parse_tags(values: list[str] | None) -> list[str]:
    tags: list[str] = []
    for value in values or []:
        for item in value.split(";"):
            tag = item.strip()
            if tag:
                tags.append(tag)
    return tags


def normalize_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        key = tag.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(tag.strip())
    return result


def format_tags(tags: list[str] | None) -> str:
    return ", ".join(tags or []) if tags else "-"


def get_attachments(work_item: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in work_item.get("relations", []) or []
        if item.get("rel") == "AttachedFile"
    ]


def load_work_item_payload(
    *,
    fixture: str | None,
    project: str | None,
    work_item_id: int,
    include_comments: bool = False,
) -> dict[str, Any]:
    if fixture:
        data = load_fixture(fixture)
        if "work_item" not in data:
            raise ValueError("fixture must contain 'work_item'")
        return data

    repo = get_repository()
    payload: dict[str, Any] = {
        "work_item": repo.get_work_item(
            work_item_id,
            project=project,
            expand_relations=True,
        )
    }
    if include_comments:
        payload["comments"] = repo.get_work_item_comments(work_item_id, project=project)
    return payload


def load_work_item_only(
    *,
    fixture: str | None,
    project: str | None,
    work_item_id: int,
) -> tuple[dict[str, Any], Any | None]:
    if fixture:
        data = load_fixture(fixture)
        if "work_item" not in data:
            raise ValueError("fixture must contain 'work_item'")
        return data["work_item"], None

    repo = get_repository()
    return (
        repo.get_work_item(work_item_id, project=project, expand_relations=True),
        repo,
    )


def write_output(markdown: str, output: str | None) -> None:
    if output:
        Path(output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)


def json_patch_replace(path: str, value: Any) -> dict[str, Any]:
    return {"op": "add", "path": path, "value": value}


def render_write_result(result: dict[str, Any]) -> list[str]:
    lines = [
        f"- Dry-run: {value_or_dash(result.get('dry_run'))}",
        f"- Work item: {value_or_dash(result.get('work_item_id'))}",
    ]
    if "new_rev" in result:
        lines.append(f"- New revision: {value_or_dash(result.get('new_rev'))}")
    if result.get("changed_fields"):
        lines.append(f"- Changed fields: {', '.join(result.get('changed_fields') or [])}")
    if result.get("comment_id"):
        lines.append(f"- Comment ID: {value_or_dash(result.get('comment_id'))}")
    if result.get("url"):
        lines.append(f"- URL: {value_or_dash(result.get('url'))}")
    return lines
