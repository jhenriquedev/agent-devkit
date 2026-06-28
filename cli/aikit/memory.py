"""Local AI DevKit memory and napkin helpers."""

from __future__ import annotations

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.aikit.llm import config_home, config_path, load_config, save_config


def memory_home() -> Path:
    return config_home() / "memory"


def normalize_prompt(prompt: str) -> str:
    text = " ".join(prompt.lower().split())
    return text[:160]


def napkin_context(root: Path, *, agent_id: str | None = None, source_id: str | None = None) -> dict[str, Any]:
    paths = [
        root / "vendor" / "skills" / "napkin" / "napkin.md",
        memory_home() / "global" / "napkin.md",
    ]
    if agent_id:
        paths.append(memory_home() / "agents" / agent_id / "napkin.md")
    if source_id:
        paths.append(memory_home() / "sources" / source_id / "napkin.md")
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
    config = load_config()
    memory = config.get("memory") if isinstance(config.get("memory"), dict) else {}
    usage = memory.get("usage") if isinstance(memory.get("usage"), dict) else {}
    return {
        "kind": "memory",
        "status": "ok",
        "config_path": str(config_path()),
        "memory_home": str(memory_home()),
        "usage": {
            "prompts": sorted_usage(usage.get("prompts") or {}),
            "routes": sorted_usage(usage.get("routes") or {}),
            "sources": sorted_usage(usage.get("sources") or {}),
        },
        "napkin": napkin_context(root, agent_id=agent_id, source_id=source_id),
    }


def reset_memory(*, all_memory: bool = False, agent_id: str | None = None, source_id: str | None = None) -> dict[str, Any]:
    config = load_config()
    removed_paths: list[str] = []
    if all_memory or not agent_id and not source_id:
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
    written_path = save_config(config)
    return {
        "kind": "memory-reset",
        "status": "reset",
        "config_path": str(written_path),
        "removed_paths": removed_paths,
        "sources_preserved": True,
    }


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
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value)
