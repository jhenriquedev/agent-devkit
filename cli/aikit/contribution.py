"""Contribution preparation MVP for local Agent DevKit extensions."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from cli.aikit.extensions import load_extensions
from cli.aikit.memory import sanitize_segment


CONTRIBUTION_SCHEMA_VERSION = "agent-devkit.contribution/v1"
SECRET_PATTERN = re.compile(r"(token|secret|password|api[_-]?key|pat)\s*[:=]", re.IGNORECASE)
PRIVATE_URL_PATTERN = re.compile(r"https?://(?:localhost|127\.0\.0\.1|10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[0-1])\.)", re.IGNORECASE)
LOCAL_PATH_PATTERN = re.compile(r"(/Users/|/home/|C:\\\\Users\\\\)")
PII_PATTERN = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
CORPORATE_TERMS_ENV = "AGENT_DEVKIT_CORPORATE_TERMS"


def contribution_list() -> dict[str, Any]:
    extensions = load_extensions()["extensions"]
    return {
        "kind": "contributions",
        "schema_version": CONTRIBUTION_SCHEMA_VERSION,
        "status": "ok",
        "items": [
            {
                "id": item.get("id"),
                "path": sanitize_path_for_report(item.get("path")),
                "path_sanitized": True,
                "enabled": item.get("enabled") is True,
            }
            for item in extensions
        ],
    }


def contribution_checklist(extension_id: str) -> dict[str, Any]:
    extension = find_extension(extension_id)
    if not extension:
        return {
            "kind": "contribution-checklist",
            "schema_version": CONTRIBUTION_SCHEMA_VERSION,
            "status": "blocked",
            "exit_code": 2,
            "extension_id": extension_id,
            "checks": [{"id": "extension-exists", "status": "failed"}],
        }
    checks = contribution_checks(Path(str(extension.get("path") or "")))
    return {
        "kind": "contribution-checklist",
        "schema_version": CONTRIBUTION_SCHEMA_VERSION,
        "status": "passed" if all(check["status"] == "passed" for check in checks) else "blocked",
        "exit_code": 0 if all(check["status"] == "passed" for check in checks) else 2,
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
    status = "planned" if checklist["status"] == "passed" else "blocked"
    return {
        "kind": "contribution-prepare",
        "schema_version": CONTRIBUTION_SCHEMA_VERSION,
        "status": status,
        "exit_code": 0 if status == "planned" else 2,
        "extension_id": extension_id,
        "checklist": checklist,
        "creates_pr": False,
    }


def contribution_pr(extension_id: str, *, dry_run: bool = True, yes: bool = False) -> dict[str, Any]:
    checklist = contribution_checklist(extension_id)
    safe_id = sanitize_segment(extension_id)
    plan = {
        "external_writes": True,
        "requires_confirmation": True,
        "mode": "dry-run" if dry_run or not yes else "apply",
        "commands": [
            f"git checkout -b feat/contribution-{safe_id}",
            "git add <sanitized-extension-files>",
            f"git commit -m 'Add Agent DevKit contribution {safe_id}'",
            "gh pr create --fill",
        ],
        "stores_secret": False,
        "local_paths_sanitized": True,
    }
    if checklist["status"] != "passed":
        return {
            "kind": "contribution-pr",
            "schema_version": CONTRIBUTION_SCHEMA_VERSION,
            "status": "blocked",
            "exit_code": 2,
            "extension_id": extension_id,
            "checklist": checklist,
            "plan": plan,
            "reason": "contribution_checklist_failed",
        }
    if dry_run or not yes:
        return {
            "kind": "contribution-pr",
            "schema_version": CONTRIBUTION_SCHEMA_VERSION,
            "status": "planned",
            "exit_code": 0,
            "extension_id": extension_id,
            "checklist": checklist,
            "plan": plan,
            "message": "PR contribution plan generated in report-only mode.",
        }
    return {
        "kind": "contribution-pr",
        "schema_version": CONTRIBUTION_SCHEMA_VERSION,
        "status": "blocked",
        "exit_code": 2,
        "extension_id": extension_id,
        "checklist": checklist,
        "plan": plan,
        "reason": "external_write_confirmation_required",
        "next_steps": [
            "Review the generated plan and run the git/gh commands manually or through a future confirmed writer.",
            "Agent DevKit does not open contribution PRs automatically from this runtime path.",
        ],
    }


def contribution_review(extension_id: str) -> dict[str, Any]:
    checklist = contribution_checklist(extension_id)
    return {
        "kind": "contribution-review",
        "schema_version": CONTRIBUTION_SCHEMA_VERSION,
        "status": checklist["status"],
        "exit_code": 0 if checklist["status"] == "passed" else 2,
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
    corporate_terms = configured_corporate_terms()
    structure = extension_structure_kind(path)
    return [
        {"id": "extension-exists", "status": "passed" if path.exists() else "failed"},
        {
            "id": "recognized-extension-structure",
            "status": "passed" if structure else "failed",
            "type": structure or "unknown",
        },
        {"id": "no-secret-literals", "status": "failed" if SECRET_PATTERN.search(text) else "passed"},
        {"id": "no-private-url", "status": "failed" if PRIVATE_URL_PATTERN.search(text) else "passed"},
        {"id": "no-local-path", "status": "failed" if LOCAL_PATH_PATTERN.search(text) else "passed"},
        {"id": "no-pii", "status": "failed" if PII_PATTERN.search(text) else "passed"},
        {
            "id": "no-corporate-name",
            "status": "failed" if contains_configured_corporate_term(text, corporate_terms) else "passed",
            "terms_configured": len(corporate_terms),
        },
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


def extension_structure_kind(path: Path) -> str | None:
    if not path.exists():
        return None
    if path.is_file():
        if path.suffix in {".py", ".sh"}:
            return "script"
        if path.suffix in {".md", ".yaml", ".yml", ".json"}:
            return "file"
        return None
    if (path / "agent.yaml").exists():
        return "agent"
    if (path / "SKILL.md").exists() or (path / "skill.md").exists():
        return "skill"
    if any((path / name).exists() for name in ("workflow.yaml", "workflow.yml")):
        return "workflow"
    if any(path.rglob("agent.yaml")):
        return "agent"
    if any(path.rglob("SKILL.md")) or any(path.rglob("skill.md")):
        return "skill"
    if any(path.rglob("workflow.yaml")) or any(path.rglob("workflow.yml")):
        return "workflow"
    if any(child.is_file() and child.suffix in {".py", ".sh"} for child in path.rglob("*")):
        return "script"
    return None


def sanitize_path_for_report(value: Any) -> str | None:
    if not value:
        return None
    name = Path(str(value)).name
    return f"<local-extension-path>/{sanitize_segment(name)}"


def configured_corporate_terms() -> list[str]:
    raw = os.environ.get(CORPORATE_TERMS_ENV, "")
    terms = [term.strip().lower() for term in re.split(r"[,;\n]+", raw) if len(term.strip()) >= 3]
    return sorted(set(terms))


def contains_configured_corporate_term(text: str, terms: list[str]) -> bool:
    if not terms:
        return False
    lowered = text.lower()
    return any(term in lowered for term in terms)
