"""Persistent local decisions for tools, integrations, skills and LLMs."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.aikit.app_home import app_path, ensure_app_home


DECISION_VERSION = 1
VALID_CATEGORIES = {"tools", "integrations", "skills", "llms"}
VALID_STATES = {"enabled", "disabled_by_user", "denied_by_user", "needs_setup", "unavailable", "available", "requires_permission"}
ITEM_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


def decisions_path() -> Path:
    ensure_app_home()
    path = app_path("config", "decisions.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def empty_decisions() -> dict[str, Any]:
    return {"version": DECISION_VERSION, "items": {}}


def load_decisions() -> dict[str, Any]:
    path = decisions_path()
    if not path.exists():
        return empty_decisions()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty_decisions()
    if not isinstance(data, dict):
        return empty_decisions()
    data.setdefault("version", DECISION_VERSION)
    if not isinstance(data.get("items"), dict):
        data["items"] = {}
    return data


def save_decisions(data: dict[str, Any]) -> Path:
    path = decisions_path()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def list_decisions(category: str | None = None) -> dict[str, Any]:
    data = load_decisions()
    items = [public_decision(item) for item in data.get("items", {}).values() if not category or item.get("category") == category]
    items.sort(key=lambda item: (item["category"], item["id"]))
    return {
        "kind": "decisions",
        "status": "ok",
        "category": category,
        "path": str(decisions_path()),
        "items": items,
    }


def set_decision(
    category: str,
    item_id: str,
    state: str,
    *,
    reason: str | None = None,
    scope: str = "persistent",
) -> dict[str, Any]:
    validate_category(category)
    validate_item_id(item_id)
    if state not in VALID_STATES:
        raise ValueError(f"invalid decision state: {state}")
    data = load_decisions()
    key = decision_key(category, item_id)
    item = {
        "key": key,
        "category": category,
        "id": item_id,
        "state": state,
        "scope": scope,
        "reason": reason,
        "updated_at": now_iso(),
    }
    existing = data["items"].get(key)
    if isinstance(existing, dict) and existing.get("created_at"):
        item["created_at"] = existing["created_at"]
    else:
        item["created_at"] = item["updated_at"]
    data["items"][key] = item
    path = save_decisions(data)
    return {
        "kind": "decision",
        "status": "updated",
        "path": str(path),
        "item": public_decision(item),
        "category": category,
        "id": item_id,
        "state": state,
    }


def get_decision(category: str, item_id: str) -> dict[str, Any] | None:
    validate_category(category)
    validate_item_id(item_id)
    item = load_decisions().get("items", {}).get(decision_key(category, item_id))
    return public_decision(item) if isinstance(item, dict) else None


def reset_decisions(category: str | None = None) -> dict[str, Any]:
    data = load_decisions()
    if category:
        validate_category(category)
        data["items"] = {key: value for key, value in data.get("items", {}).items() if value.get("category") != category}
    else:
        data["items"] = {}
    path = save_decisions(data)
    return {"kind": "decisions-reset", "status": "reset", "category": category, "path": str(path)}


def forget_decision(category: str, item_id: str) -> dict[str, Any]:
    validate_category(category)
    validate_item_id(item_id)
    data = load_decisions()
    key = decision_key(category, item_id)
    removed = data.get("items", {}).pop(key, None)
    path = save_decisions(data)
    return {
        "kind": "decision-forget",
        "status": "forgotten" if isinstance(removed, dict) else "not-found",
        "path": str(path),
        "category": category,
        "id": item_id,
        "removed": public_decision(removed) if isinstance(removed, dict) else None,
    }


def is_disabled(category: str, item_id: str) -> bool:
    decision = get_decision(category, item_id)
    return bool(decision and decision.get("state") in {"disabled_by_user", "denied_by_user"})


def public_decision(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "category": item.get("category"),
        "id": item.get("id"),
        "state": item.get("state"),
        "scope": item.get("scope"),
        "reason": item.get("reason"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
    }


def decision_key(category: str, item_id: str) -> str:
    return f"{category}:{item_id}"


def validate_category(category: str) -> None:
    if category not in VALID_CATEGORIES:
        available = ", ".join(sorted(VALID_CATEGORIES))
        raise ValueError(f"invalid decision category: {category}. available: {available}")


def validate_item_id(item_id: str) -> None:
    if not item_id or not ITEM_ID_PATTERN.fullmatch(item_id):
        raise ValueError("item id must use letters, numbers, dots, dashes, underscores or colons")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
