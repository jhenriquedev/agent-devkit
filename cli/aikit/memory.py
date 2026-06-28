"""Local AI DevKit memory and napkin helpers."""

from __future__ import annotations

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.aikit.app_home import (
    app_path,
    cache_home,
    ensure_app_home,
    memory_home as app_memory_home,
    sessions_home,
    tasks_home,
)
from cli.aikit.llm import config_path, load_config, save_config


SECRET_VALUE_PATTERN = re.compile(
    r"(?i)\b("
    r"sk-[a-z0-9_-]{12,}|"
    r"npm_[a-z0-9]{12,}|"
    r"gh[pousr]_[a-z0-9_]{12,}|"
    r"xox[baprs]-[a-z0-9-]{12,}|"
    r"AKIA[0-9A-Z]{12,}|"
    r"ASIA[0-9A-Z]{12,}"
    r")\b"
)
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)([\"']?)([a-z0-9_]*(?:token|secret|password|passwd|pwd|senha|chave|api[_-]?key|private[_-]?key)[a-z0-9_]*)([\"']?)(\s*[:=]\s*)([\"']?)([^\s,;}\"']+)([\"']?)"
)

MEMORY_FILE_TEMPLATES: dict[str, str] = {
    "profile.md": """# Profile

Local user profile for Agent DevKit.

## User

- Name:
- Primary language:
- Timezone:

## Notes

- Add stable facts the agent should remember.
""",
    "personality.md": """# Personality

Configured public identity and response style for Agent DevKit.

## Agent

- Name: Agent DevKit

## Style

- Tone: direct
- Detail level: concise
""",
    "preferences.md": """# Preferences

Reusable user preferences.

## Defaults

- Prefer local-first execution.
- Ask before external writes.
""",
    "projects.md": """# Projects

Frequently used projects and repositories.

## Items

- Add project names, paths, and non-secret references here.
""",
    "routines.md": """# Routines

Recurring workflows, checks, and habits.

## Items

- Add routines that should be easy to reuse.
""",
    "napkin.md": """# Agent DevKit Napkin

Curated local runbook entries promoted from repeated use.

## Execution & Validation

- Keep high-value reusable notes here.
""",
}


def memory_home() -> Path:
    return app_memory_home()


def ensure_memory() -> dict[str, Any]:
    ensure_app_home()
    home = memory_home()
    home.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, Any]] = []
    created: list[str] = []
    for name, template in MEMORY_FILE_TEMPLATES.items():
        path = home / name
        if not path.exists():
            path.write_text(template, encoding="utf-8")
            created.append(str(path))
        files.append({"name": name, "path": str(path), "exists": path.exists()})
    return {
        "kind": "memory-path",
        "status": "ok",
        "home": str(home),
        "created": created,
        "files": files,
    }


def normalize_prompt(prompt: str) -> str:
    text = " ".join(redact_secrets(prompt).lower().split())
    return text[:160]


def redact_secrets(value: str) -> str:
    redacted = SECRET_VALUE_PATTERN.sub("[REDACTED_SECRET]", value)
    return SECRET_ASSIGNMENT_PATTERN.sub(r"\1\2\3\4\5[REDACTED_SECRET]\7", redacted)


def napkin_context(root: Path, *, agent_id: str | None = None, source_id: str | None = None) -> dict[str, Any]:
    paths = [
        root / "vendor" / "skills" / "napkin" / "napkin.md",
        memory_home() / "napkin.md",
        memory_home() / "global" / "napkin.md",
    ]
    if agent_id:
        paths.append(memory_home() / "agents" / sanitize_segment(agent_id) / "napkin.md")
    if source_id:
        paths.append(memory_home() / "sources" / sanitize_segment(source_id) / "napkin.md")
    return {
        "loaded": any(path.exists() for path in paths),
        "paths": [
            {
                "path": str(path),
                "exists": path.exists(),
            }
            for path in paths
        ],
    }


def record_usage(
    prompt: str,
    *,
    route: dict[str, Any] | None = None,
    source_id: str | None = None,
) -> None:
    config = load_config()
    memory = config.setdefault("memory", {})
    usage = memory.setdefault("usage", {})
    now = datetime.now(timezone.utc).isoformat()
    increment_bucket(usage.setdefault("prompts", {}), normalize_prompt(prompt), now)
    if route:
        route_key = f"{route.get('agent_id')}/{route.get('capability_id')}"
        increment_bucket(usage.setdefault("routes", {}), route_key, now)
    if source_id:
        increment_bucket(usage.setdefault("sources", {}), source_id, now)
    save_config(config)


def show_memory(root: Path, *, agent_id: str | None = None, source_id: str | None = None) -> dict[str, Any]:
    memory_paths = ensure_memory()
    config = load_config()
    memory = config.get("memory") if isinstance(config.get("memory"), dict) else {}
    usage = memory.get("usage") if isinstance(memory.get("usage"), dict) else {}
    return {
        "kind": "memory",
        "status": "ok",
        "config_path": str(config_path()),
        "memory_home": str(memory_home()),
        "files": memory_paths["files"],
        "usage": {
            "prompts": sorted_usage(usage.get("prompts") or {}),
            "routes": sorted_usage(usage.get("routes") or {}),
            "sources": sorted_usage(usage.get("sources") or {}),
        },
        "napkin": napkin_context(root, agent_id=agent_id, source_id=source_id),
    }


def reset_memory(
    *,
    all_memory: bool = False,
    agent_id: str | None = None,
    source_id: str | None = None,
    reset_sessions: bool = False,
    reset_tasks: bool = False,
    reset_cache: bool = False,
) -> dict[str, Any]:
    config = load_config()
    removed_paths: list[str] = []
    scoped_reset = any([agent_id, source_id, reset_sessions, reset_tasks, reset_cache])
    if all_memory or not scoped_reset:
        config.pop("memory", None)
        if memory_home().exists():
            removed_paths.append(str(memory_home()))
            shutil.rmtree(memory_home())
    else:
        memory = config.get("memory") if isinstance(config.get("memory"), dict) else {}
        usage = memory.get("usage") if isinstance(memory.get("usage"), dict) else {}
        if agent_id:
            usage.get("routes", {}).pop(agent_id, None)
            path = memory_home() / "agents" / sanitize_segment(agent_id)
            remove_path(path, removed_paths)
        if source_id:
            usage.get("sources", {}).pop(source_id, None)
            path = memory_home() / "sources" / sanitize_segment(source_id)
            remove_path(path, removed_paths)
    if all_memory or reset_sessions:
        remove_path(sessions_home(), removed_paths)
        remove_path(app_path("state", "active-session.json"), removed_paths)
    if all_memory or reset_tasks:
        remove_path(tasks_home(), removed_paths)
    if all_memory or reset_cache:
        remove_path(cache_home(), removed_paths)
    ensure_app_home()
    written_path = save_config(config)
    return {
        "kind": "memory-reset",
        "status": "reset",
        "config_path": str(written_path),
        "removed_paths": removed_paths,
        "sources_preserved": True,
        "sessions_reset": bool(all_memory or reset_sessions),
        "tasks_reset": bool(all_memory or reset_tasks),
        "cache_reset": bool(all_memory or reset_cache),
    }


def memory_path_payload() -> dict[str, Any]:
    return ensure_memory()


def increment_bucket(bucket: dict[str, Any], key: str, now: str) -> None:
    item = bucket.setdefault(key, {"count": 0, "first_seen": now, "last_seen": now})
    item["count"] = int(item.get("count") or 0) + 1
    item.setdefault("first_seen", now)
    item["last_seen"] = now


def sorted_usage(bucket: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    for key, value in bucket.items():
        if isinstance(value, dict):
            items.append({"key": key, **value})
    return sorted(items, key=lambda item: (-int(item.get("count") or 0), item["key"]))


def remove_path(path: Path, removed_paths: list[str]) -> None:
    if path.exists():
        removed_paths.append(str(path))
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def sanitize_segment(value: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip(".-")
    return sanitized or "item"
