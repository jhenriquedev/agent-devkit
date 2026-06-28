"""Local task and scheduler primitives for Agent DevKit."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from cli.aikit.app_home import ensure_app_home, tasks_home
from cli.aikit.memory import redact_secrets
from cli.aikit.permissions import permission_check, provider_for_agent


TASK_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_tasks_home() -> Path:
    ensure_app_home()
    home = tasks_home()
    (home / "history").mkdir(parents=True, exist_ok=True)
    return home


def tasks_path() -> Path:
    return ensure_tasks_home() / "tasks.json"


def history_path(task_id: str) -> Path:
    return ensure_tasks_home() / "history" / f"{safe_task_id(task_id)}.md"


def load_tasks() -> dict[str, Any]:
    path = tasks_path()
    if not path.exists():
        return {"version": 1, "tasks": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": 1, "tasks": []}
    if not isinstance(data, dict):
        return {"version": 1, "tasks": []}
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        data["tasks"] = []
    data.setdefault("version", 1)
    return data


def save_tasks(data: dict[str, Any]) -> Path:
    path = tasks_path()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def list_tasks() -> dict[str, Any]:
    data = load_tasks()
    return {
        "kind": "tasks",
        "status": "ok",
        "path": str(tasks_path()),
        "items": [public_task(item) for item in data["tasks"] if isinstance(item, dict)],
    }


def create_task(
    *,
    task_id: str | None = None,
    title: str | None = None,
    prompt: str | None = None,
    schedule: dict[str, Any] | None = None,
    action: dict[str, Any] | None = None,
    permissions: dict[str, Any] | None = None,
    notifications: list[dict[str, Any]] | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    data = load_tasks()
    raw_id = task_id or slugify(title or prompt or "task")
    task_id = unique_task_id(raw_id, data)
    created_at = now_iso()
    task = {
        "id": task_id,
        "title": title or prompt or task_id,
        "status": "enabled" if enabled else "disabled",
        "created_at": created_at,
        "updated_at": created_at,
        "schedule": schedule or {"type": "manual"},
        "action": action or {"type": "prompt", "prompt": redact_secrets(prompt or "")},
        "permissions": permissions or {"mode": "report-only"},
        "notifications": notifications or [{"type": "terminal"}],
        "run_count": 0,
    }
    data["tasks"].append(task)
    save_tasks(data)
    append_history(task_id, f"Created task `{task_id}`.")
    return {"kind": "task", "status": "created", "task": public_task(task), "path": str(tasks_path())}


def show_task(task_id: str) -> dict[str, Any]:
    task = find_task(task_id)
    return {"kind": "task", "status": "ok", "task": public_task(task), "path": str(tasks_path())}


def task_history(task_id: str) -> dict[str, Any]:
    task = find_task(task_id)
    path = history_path(str(task["id"]))
    return {
        "kind": "task-history",
        "status": "ok",
        "task": public_task(task),
        "path": str(path),
        "history": path.read_text(encoding="utf-8") if path.exists() else "",
    }


def run_task(task_id: str, *, dry_run: bool = False) -> dict[str, Any]:
    data = load_tasks()
    task = find_task_in_data(data, task_id)
    if task.get("status") in {"paused", "disabled"}:
        return {"kind": "task-run", "status": "skipped", "ok": False, "task": public_task(task), "message": "Task is not enabled.", "exit_code": 2}
    preview = task_run_preview(task)
    if dry_run:
        return {"kind": "task-run", "status": "planned", "ok": True, "dry_run": True, "task": public_task(task), "preview": preview}
    permission = task_external_write_permission(task)
    if not permission["ok"]:
        append_history(str(task["id"]), f"Blocked task `{task['id']}` because it requires external write permission.")
        return {
            "kind": "task-run",
            "status": "blocked",
            "ok": False,
            "dry_run": False,
            "task": public_task(task),
            "preview": preview,
            "permission": permission,
            "requires_permission": True,
            "message": "Task declares external_writes=true and does not have explicit external write permission.",
            "exit_code": 2,
        }
    task["run_count"] = int(task.get("run_count") or 0) + 1
    task["last_run_at"] = now_iso()
    task["updated_at"] = task["last_run_at"]
    save_tasks(data)
    append_history(str(task["id"]), f"Executed task `{task['id']}` in local scheduler.")
    return {"kind": "task-run", "status": "ok", "ok": True, "dry_run": False, "task": public_task(task), "preview": preview}


def scheduler_run_once(*, dry_run: bool = False) -> dict[str, Any]:
    data = load_tasks()
    due = [item for item in data["tasks"] if isinstance(item, dict) and item.get("status") == "enabled" and task_is_due(item)]
    runs = [run_task(str(item["id"]), dry_run=dry_run) for item in due]
    return {"kind": "scheduler", "status": "ok", "dry_run": dry_run, "due_count": len(due), "runs": runs}


def update_task_status(task_id: str, status: str) -> dict[str, Any]:
    data = load_tasks()
    task = find_task_in_data(data, task_id)
    task["status"] = status
    task["updated_at"] = now_iso()
    save_tasks(data)
    append_history(str(task["id"]), f"Status changed to `{status}`.")
    return {"kind": "task", "status": "updated", "task": public_task(task), "path": str(tasks_path())}


def update_task_schedule(task_id: str, *, every: str | None = None, cron: str | None = None) -> dict[str, Any]:
    data = load_tasks()
    task = find_task_in_data(data, task_id)
    if every:
        task["schedule"] = {"type": "interval", "every": every}
    if cron:
        task["schedule"] = {"type": "cron", "cron": cron}
    task["updated_at"] = now_iso()
    save_tasks(data)
    append_history(str(task["id"]), "Schedule updated.")
    return {"kind": "task", "status": "updated", "task": public_task(task), "path": str(tasks_path())}


def delete_task(task_id: str, *, yes: bool = False) -> dict[str, Any]:
    if not yes:
        return {"kind": "task", "status": "needs-confirmation", "ok": False, "message": "Deleting a task requires --yes.", "exit_code": 2}
    data = load_tasks()
    task = find_task_in_data(data, task_id)
    data["tasks"] = [item for item in data["tasks"] if not isinstance(item, dict) or item.get("id") != task.get("id")]
    save_tasks(data)
    append_history(str(task["id"]), "Task deleted.")
    return {"kind": "task", "status": "deleted", "task": public_task(task), "path": str(tasks_path())}


def reset_tasks() -> list[str]:
    home = tasks_home()
    removed: list[str] = []
    if home.exists():
        removed.append(str(home))
        shutil.rmtree(home)
    ensure_tasks_home()
    return removed


def public_task(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": task.get("id"),
        "title": task.get("title"),
        "status": task.get("status"),
        "created_at": task.get("created_at"),
        "updated_at": task.get("updated_at"),
        "schedule": task.get("schedule") or {},
        "action": task.get("action") or {},
        "permissions": task.get("permissions") or {},
        "notifications": task.get("notifications") or [],
        "run_count": int(task.get("run_count") or 0),
        "last_run_at": task.get("last_run_at"),
    }


def task_run_preview(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action") if isinstance(task.get("action"), dict) else {}
    return {
        "task_id": task.get("id"),
        "action_type": action.get("type"),
        "agent": action.get("agent"),
        "capability": action.get("capability"),
        "prompt": action.get("prompt"),
        "external_writes": bool(action.get("external_writes")),
        "permissions": task.get("permissions") or {},
    }


def task_requires_external_write_permission(task: dict[str, Any]) -> bool:
    return not task_external_write_permission(task)["ok"]


def task_is_due(task: dict[str, Any], *, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    schedule = task.get("schedule") if isinstance(task.get("schedule"), dict) else {}
    schedule_type = schedule.get("type") or "manual"
    if schedule_type == "manual":
        return False
    last_run_at = parse_iso_datetime(task.get("last_run_at"))
    if schedule_type == "interval":
        interval = parse_interval(str(schedule.get("every") or ""))
        if interval is None:
            return False
        return last_run_at is None or last_run_at + interval <= now
    if schedule_type == "daily":
        scheduled_time = parse_time(str(schedule.get("time") or "00:00")) or time(0, 0)
        if now.time().replace(tzinfo=None) < scheduled_time:
            return False
        return last_run_at is None or last_run_at.date() < now.date()
    if schedule_type == "cron":
        # Full cron parsing is outside the local MVP; run once after creation
        # and require an external scheduler for precise recurrence.
        return last_run_at is None
    return False


def parse_interval(value: str) -> timedelta | None:
    match = re.fullmatch(r"\s*(\d+)\s*([mhd])\s*", value.lower())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    if amount <= 0:
        return None
    if unit == "m":
        return timedelta(minutes=amount)
    if unit == "h":
        return timedelta(hours=amount)
    return timedelta(days=amount)


def parse_time(value: str) -> time | None:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return None


def parse_iso_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def task_external_write_permission(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action") if isinstance(task.get("action"), dict) else {}
    permissions = task.get("permissions") if isinstance(task.get("permissions"), dict) else {}
    if not bool(action.get("external_writes")):
        return {"ok": True, "status": "allowed", "requires_permission": False}
    if bool(permissions.get("external_writes_allowed")):
        return {"ok": True, "status": "allowed", "source": "task-permission", "requires_permission": False}
    agent = action.get("agent")
    provider = action.get("provider") or provider_for_agent(str(agent) if agent else None)
    check = permission_check(
        agent=str(agent) if agent else None,
        provider=str(provider) if provider else None,
        action=str(permissions.get("required_action") or action.get("required_action") or "write"),
        task_id=str(task.get("id") or ""),
    )
    return check


def find_task(task_id: str) -> dict[str, Any]:
    return find_task_in_data(load_tasks(), task_id)


def find_task_in_data(data: dict[str, Any], task_id: str) -> dict[str, Any]:
    resolved = safe_task_id(task_id)
    for item in data.get("tasks", []):
        if isinstance(item, dict) and item.get("id") == resolved:
            return item
    raise ValueError(f"task not found: {task_id}")


def append_history(task_id: str, message: str) -> None:
    path = history_path(task_id)
    line = f"- {now_iso()} {redact_secrets(message)}\n"
    with path.open("a", encoding="utf-8") as file:
        file.write(line)


def unique_task_id(task_id: str, data: dict[str, Any]) -> str:
    base = safe_task_id(task_id)
    existing = {item.get("id") for item in data.get("tasks", []) if isinstance(item, dict)}
    if base not in existing:
        return base
    index = 2
    while f"{base}-{index}" in existing:
        index += 1
    return f"{base}-{index}"


def safe_task_id(task_id: str) -> str:
    if not TASK_ID_PATTERN.fullmatch(task_id):
        return slugify(task_id)
    return task_id


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.lower()).strip(".-")
    return slug[:80] or "task"
