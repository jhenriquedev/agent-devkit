"""Contribution preparation MVP for local Agent DevKit extensions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cli.aikit.extensions import load_extensions


CONTRIBUTION_SCHEMA_VERSION = "agent-devkit.contribution/v1"
SECRET_PATTERN = re.compile(r"(token|secret|password|api[_-]?key|pat)\s*[:=]", re.IGNORECASE)
PRIVATE_URL_PATTERN = re.compile(r"https?://(?:localhost|127\.0\.0\.1|10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[0-1])\.)", re.IGNORECASE)
LOCAL_PATH_PATTERN = re.compile(r"(/Users/|/home/|C:\\\\Users\\\\)")


def contribution_list() -> dict[str, Any]:
    extensions = load_extensions()["extensions"]
    return {
        "kind": "contributions",
        "schema_version": CONTRIBUTION_SCHEMA_VERSION,
        "status": "ok",
        "items": [{"id": item.get("id"), "path": item.get("path"), "enabled": item.get("enabled") is True} for item in extensions],
    }


def contribution_checklist(extension_id: str) -> dict[str, Any]:
    extension = find_extension(extension_id)
    if not extension:
        return {
            "kind": "contribution-checklist",
            "schema_version": CONTRIBUTION_SCHEMA_VERSION,
            "status": "blocked",
            "extension_id": extension_id,
            "checks": [{"id": "extension-exists", "status": "failed"}],
        }
    checks = contribution_checks(Path(str(extension.get("path") or "")))
    return {
        "kind": "contribution-checklist",
        "schema_version": CONTRIBUTION_SCHEMA_VERSION,
        "status": "passed" if all(check["status"] == "passed" for check in checks) else "blocked",
        "extension_id": extension_id,
        "checks": checks,
        "requires_human_confirmation_for_pr": True,
    }


def contribution_validate(extension_id: str) -> dict[str, Any]:
    payload = contribution_checklist(extension_id)
    payload["kind"] = "contribution-validation"
    return payload


def contribution_prepare(extension_id: str) -> dict[str, Any]:
    checklist = contribution_checklist(extension_id)
    return {
        "kind": "contribution-prepare",
        "schema_version": CONTRIBUTION_SCHEMA_VERSION,
        "status": "planned" if checklist["status"] == "passed" else "blocked",
        "extension_id": extension_id,
        "checklist": checklist,
        "creates_pr": False,
    }


def contribution_review(extension_id: str) -> dict[str, Any]:
    checklist = contribution_checklist(extension_id)
    return {
        "kind": "contribution-review",
        "schema_version": CONTRIBUTION_SCHEMA_VERSION,
        "status": checklist["status"],
        "extension_id": extension_id,
        "findings": [check for check in checklist["checks"] if check["status"] != "passed"],
    }


def find_extension(extension_id: str) -> dict[str, Any] | None:
    for item in load_extensions()["extensions"]:
        if item.get("id") == extension_id:
            return item
    return None


def contribution_checks(path: Path) -> list[dict[str, Any]]:
    text = read_extension_text(path)
    return [
        {"id": "extension-exists", "status": "passed" if path.exists() else "failed"},
        {"id": "no-secret-literals", "status": "failed" if SECRET_PATTERN.search(text) else "passed"},
        {"id": "no-private-url", "status": "failed" if PRIVATE_URL_PATTERN.search(text) else "passed"},
        {"id": "no-local-path", "status": "failed" if LOCAL_PATH_PATTERN.search(text) else "passed"},
        {"id": "human-pr-confirmation", "status": "passed"},
    ]


def read_extension_text(path: Path) -> str:
    if not path.exists():
        return ""
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="ignore")[:200_000]
    chunks = []
    for child in sorted(path.rglob("*")):
        if child.is_file() and child.suffix in {".md", ".yaml", ".yml", ".json", ".py", ".sh", ".txt"}:
            chunks.append(child.read_text(encoding="utf-8", errors="ignore")[:50_000])
    return "\n".join(chunks)[:300_000]
