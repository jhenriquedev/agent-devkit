"""Local permission policy helpers for Agent DevKit."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.aikit.app_home import ensure_app_home, policies_home
from cli.aikit.memory import redact_secrets


PERMISSION_LEVELS = (
    "read-only",
    "draft-only",
    "comment-with-approval",
    "write-with-approval",
    "auto-write",
    "admin",
)
DEFAULT_PERMISSION_LEVEL = "read-only"
PROVIDER_BY_AGENT = {
    "github-pr-reviewer": "github",
}
ACTION_REQUIRED_LEVEL = {
    "read": "read-only",
    "draft": "draft-only",
    "comment": "comment-with-approval",
    "write": "write-with-approval",
    "approve": "write-with-approval",
    "request-changes": "write-with-approval",
    "admin": "admin",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_policies_home() -> Path:
    ensure_app_home()
    home = policies_home()
    home.mkdir(parents=True, exist_ok=True)
    return home


def permissions_json_path() -> Path:
    return ensure_policies_home() / "permissions.json"


def permissions_md_path() -> Path:
    return ensure_policies_home() / "permissions.md"


def empty_policy() -> dict[str, Any]:
    return {
        "version": 1,
        "default_level": DEFAULT_PERMISSION_LEVEL,
        "grants": [],
    }


def load_permissions() -> dict[str, Any]:
    path = permissions_json_path()
    if not path.exists():
        policy = empty_policy()
        save_permissions(policy)
        return policy
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = path.with_suffix(f".corrupt-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json")
        path.replace(backup)
        data = empty_policy()
    if not isinstance(data, dict):
        data = empty_policy()
    data.setdefault("version", 1)
    data.setdefault("default_level", DEFAULT_PERMISSION_LEVEL)
    if data.get("default_level") not in PERMISSION_LEVELS:
        data["default_level"] = DEFAULT_PERMISSION_LEVEL
    if not isinstance(data.get("grants"), list):
        data["grants"] = []
    return data


def save_permissions(policy: dict[str, Any]) -> Path:
    ensure_policies_home()
    path = permissions_json_path()
    path.write_text(json.dumps(policy, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    permissions_md_path().write_text(render_permissions_md(policy), encoding="utf-8")
    return path


def show_permissions() -> dict[str, Any]:
    policy = load_permissions()
    return {
        "kind": "permissions",
        "status": "ok",
        "default_level": policy["default_level"],
        "levels": list(PERMISSION_LEVELS),
        "grants": [public_grant(item) for item in policy["grants"] if isinstance(item, dict)],
        "json_path": str(permissions_json_path()),
        "markdown_path": str(permissions_md_path()),
    }


def grant_permission(
    agent: str,
    provider: str,
    level: str,
    *,
    project: str | None = None,
    task_id: str | None = None,
) -> dict[str, Any]:
    validate_level(level)
    policy = load_permissions()
    grants = [item for item in policy["grants"] if isinstance(item, dict)]
    grant = find_grant(grants, agent=agent, provider=provider, project=project, task_id=task_id)
    timestamp = now_iso()
    if grant:
        grant["level"] = level
        grant["updated_at"] = timestamp
    else:
        grant = {
            "agent": agent,
            "provider": provider,
            "level": level,
            "project": project,
            "task_id": task_id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        grants.append(grant)
    policy["grants"] = grants
    path = save_permissions(policy)
    return {
        "kind": "permissions",
        "status": "granted",
        "grant": public_grant(grant),
        "json_path": str(path),
        "markdown_path": str(permissions_md_path()),
    }


def revoke_permission(
    agent: str,
    provider: str,
    level: str | None = None,
    *,
    project: str | None = None,
    task_id: str | None = None,
) -> dict[str, Any]:
    if level:
        validate_level(level)
    policy = load_permissions()
    removed: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []
    for item in policy["grants"]:
        if not isinstance(item, dict):
            continue
        matches = (
            item.get("agent") == agent
            and item.get("provider") == provider
            and item.get("project") == project
            and item.get("task_id") == task_id
            and (level is None or item.get("level") == level)
        )
        if matches:
            removed.append(item)
        else:
            kept.append(item)
    policy["grants"] = kept
    path = save_permissions(policy)
    return {
        "kind": "permissions",
        "status": "revoked" if removed else "not-found",
        "removed": [public_grant(item) for item in removed],
        "json_path": str(path),
        "markdown_path": str(permissions_md_path()),
    }


def permission_check(
    *,
    agent: str | None,
    provider: str | None,
    action: str,
    project: str | None = None,
    task_id: str | None = None,
) -> dict[str, Any]:
    required = required_level_for_action(action)
    resolved_provider = provider or provider_for_agent(agent)
    policy = load_permissions()
    grant = best_grant(
        policy["grants"],
        agent=agent,
        provider=resolved_provider,
        project=project,
        task_id=task_id,
    )
    granted = normalize_level(grant.get("level") if grant else policy.get("default_level", DEFAULT_PERMISSION_LEVEL))
    allowed = level_allows(granted, required)
    return {
        "kind": "permission-check",
        "status": "allowed" if allowed else "blocked",
        "ok": allowed,
        "agent": agent,
        "provider": resolved_provider,
        "action": action,
        "required_level": required,
        "granted_level": granted,
        "grant": public_grant(grant) if grant else None,
        "default_level": policy.get("default_level", DEFAULT_PERMISSION_LEVEL),
        "requires_permission": not allowed,
    }


def assert_permission(
    *,
    agent: str | None,
    provider: str | None,
    action: str,
    project: str | None = None,
    task_id: str | None = None,
) -> dict[str, Any]:
    return permission_check(agent=agent, provider=provider, action=action, project=project, task_id=task_id)


def provider_for_agent(agent: str | None) -> str | None:
    return PROVIDER_BY_AGENT.get(agent or "")


def required_level_for_action(action: str) -> str:
    return ACTION_REQUIRED_LEVEL.get(action, action if action in PERMISSION_LEVELS else "write-with-approval")


def normalize_level(level: Any) -> str:
    return str(level) if str(level) in PERMISSION_LEVELS else DEFAULT_PERMISSION_LEVEL


def level_allows(granted: str, required: str) -> bool:
    validate_level(granted)
    validate_level(required)
    return PERMISSION_LEVELS.index(granted) >= PERMISSION_LEVELS.index(required)


def validate_level(level: str) -> None:
    if level not in PERMISSION_LEVELS:
        available = ", ".join(PERMISSION_LEVELS)
        raise ValueError(f"unknown permission level: {level}. available: {available}")


def best_grant(
    grants: list[Any],
    *,
    agent: str | None,
    provider: str | None,
    project: str | None,
    task_id: str | None,
) -> dict[str, Any] | None:
    candidates = [
        item
        for item in grants
        if isinstance(item, dict)
        and item.get("agent") == agent
        and item.get("provider") == provider
        and item.get("project") in {None, project}
        and item.get("task_id") in {None, task_id}
    ]
    if not candidates:
        return None
    candidates.sort(key=grant_specificity, reverse=True)
    return candidates[0]


def find_grant(
    grants: list[dict[str, Any]],
    *,
    agent: str,
    provider: str,
    project: str | None,
    task_id: str | None,
) -> dict[str, Any] | None:
    for item in grants:
        if (
            item.get("agent") == agent
            and item.get("provider") == provider
            and item.get("project") == project
            and item.get("task_id") == task_id
        ):
            return item
    return None


def grant_specificity(grant: dict[str, Any]) -> tuple[int, int]:
    scope = int(bool(grant.get("project"))) + int(bool(grant.get("task_id")))
    return scope, PERMISSION_LEVELS.index(normalize_level(grant.get("level")))


def public_grant(grant: dict[str, Any] | None) -> dict[str, Any] | None:
    if not grant:
        return None
    return {
        "agent": grant.get("agent"),
        "provider": grant.get("provider"),
        "level": grant.get("level"),
        "project": grant.get("project"),
        "task_id": grant.get("task_id"),
        "created_at": grant.get("created_at"),
        "updated_at": grant.get("updated_at"),
    }


def render_permissions_md(policy: dict[str, Any]) -> str:
    lines = [
        "# Agent DevKit Permissions",
        "",
        f"- Default level: `{redact_secrets(str(policy.get('default_level') or DEFAULT_PERMISSION_LEVEL))}`",
        "",
        "## Levels",
        "",
    ]
    for level in PERMISSION_LEVELS:
        lines.append(f"- `{level}`")
    lines.extend(["", "## Grants", ""])
    grants = [item for item in policy.get("grants", []) if isinstance(item, dict)]
    if not grants:
        lines.append("- No explicit grants configured.")
    for item in grants:
        scope = []
        if item.get("project"):
            scope.append(f"project={item['project']}")
        if item.get("task_id"):
            scope.append(f"task={item['task_id']}")
        scope_text = f" ({', '.join(scope)})" if scope else ""
        lines.append(
            "- "
            f"`{redact_secrets(str(item.get('agent') or '-'))}` / "
            f"`{redact_secrets(str(item.get('provider') or '-'))}` -> "
            f"`{redact_secrets(str(item.get('level') or DEFAULT_PERMISSION_LEVEL))}`"
            f"{scope_text}"
        )
    lines.append("")
    return "\n".join(lines)
