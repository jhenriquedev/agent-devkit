"""Local task and scheduler primitives for Agent DevKit."""

from __future__ import annotations

import json
import re
import shutil
import uuid
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from cli.aikit.app_home import ensure_app_home, tasks_home
from cli.aikit.audit import try_record_audit
from cli.aikit.autonomy import build_task_autonomy_contract
from cli.aikit.memory import redact_secrets
from cli.aikit.notifications import maybe_notify_task
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


def scheduler_events_path() -> Path:
    return ensure_tasks_home() / "scheduled-runs.jsonl"


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
    notify: dict[str, Any] | None = None,
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
        "action": action or ({"type": "prompt", "prompt": redact_secrets(prompt)} if prompt else {"type": "noop"}),
        "permissions": permissions or {"mode": "report-only"},
        "notifications": notifications or [{"type": "terminal"}],
        "run_count": 0,
    }
    if notify is not None:
        task["notify"] = notify
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


def run_task(
    task_id: str,
    *,
    dry_run: bool = False,
    origin: str = "cli",
    run_id: str | None = None,
    scheduled_for: str | None = None,
) -> dict[str, Any]:
    data = load_tasks()
    task = find_task_in_data(data, task_id)
    scheduler_origin = origin == "scheduler"
    run_id = run_id or (new_run_id() if scheduler_origin else None)
    scheduled_for = scheduled_for or (now_iso() if scheduler_origin else None)
    started_at = now_iso() if scheduler_origin else None
    if task.get("status") in {"paused", "disabled"}:
        autonomy_contract = build_task_autonomy_contract(task, origin=origin, dry_run=dry_run)
        payload = {
            "kind": "task-run",
            "status": "skipped",
            "ok": False,
            "task": public_task(task),
            "autonomy_contract": autonomy_contract,
            "message": "Task is not enabled.",
            "exit_code": 2,
        }
        if scheduler_origin:
            attach_scheduler_metadata(
                payload,
                task,
                event="scheduled_task.skipped",
                run_id=run_id,
                scheduled_for=scheduled_for,
                started_at=started_at,
                finished_at=now_iso(),
                summary="Scheduled task was skipped because it is not enabled.",
            )
            attach_scheduler_audit(payload, task)
            attach_task_notification(payload, task, "scheduled_task.skipped", origin=origin)
            record_scheduler_event(payload)
        return payload
    preview = task_run_preview(task, origin=origin, dry_run=dry_run)
    if dry_run:
        return {
            "kind": "task-run",
            "status": "planned",
            "ok": True,
            "dry_run": True,
            "task": public_task(task),
            "preview": preview,
            "autonomy_contract": preview["autonomy_contract"],
        }
    scheduler_events: list[dict[str, Any]] = []
    if scheduler_origin:
        started_event = scheduler_event_payload(
            task,
            event="scheduled_task.started",
            status="running",
            run_id=run_id,
            scheduled_for=scheduled_for,
            started_at=started_at,
            summary=f"Scheduled task {task['id']} started.",
        )
        attach_task_notification(started_event, task, "scheduled_task.started", origin=origin)
        record_scheduler_event(started_event)
        scheduler_events.append(started_event)
    try:
        permission = task_external_write_permission(task)
        preview = task_run_preview(task, origin=origin, dry_run=dry_run, permission=permission)
        if not permission["ok"]:
            append_history(str(task["id"]), f"Blocked task `{task['id']}` because it requires external write permission.")
            payload = {
                "kind": "task-run",
                "status": "blocked",
                "ok": False,
                "dry_run": False,
                "task": public_task(task),
                "preview": preview,
                "autonomy_contract": preview["autonomy_contract"],
                "permission": permission,
                "requires_permission": True,
                "message": "Task declares external_writes=true and does not have explicit external write permission.",
                "exit_code": 2,
            }
            if scheduler_origin:
                attach_scheduler_metadata(
                    payload,
                    task,
                    event="scheduled_task.blocked",
                    run_id=run_id,
                    scheduled_for=scheduled_for,
                    started_at=started_at,
                    finished_at=now_iso(),
                    summary="Scheduled task was blocked by permission policy.",
                )
                attach_scheduler_audit(payload, task)
            attach_task_notification(payload, task, event_name(origin, "blocked"), origin=origin)
            if scheduler_origin:
                record_scheduler_event(payload)
                payload["events"] = scheduler_events + [scheduler_event_summary(payload)]
                payload["events_path"] = str(scheduler_events_path())
            return payload
        action_result = execute_task_action(task, origin=origin)
        action_ok = bool(action_result.get("ok")) or action_result.get("status") == "ok"
        if not action_ok:
            append_history(str(task["id"]), f"Task `{task['id']}` failed: {action_result.get('message') or action_result.get('status')}")
            payload = {
                "kind": "task-run",
                "status": "failed",
                "ok": False,
                "dry_run": False,
                "task": public_task(task),
                "preview": preview,
                "autonomy_contract": preview["autonomy_contract"],
                "result": action_result,
                "message": action_result.get("message") or "Task action failed.",
                "exit_code": int(action_result.get("exit_code") or 1),
            }
            if scheduler_origin:
                finished_at = now_iso()
                attach_scheduler_metadata(
                    payload,
                    task,
                    event="scheduled_task.failed",
                    run_id=run_id,
                    scheduled_for=scheduled_for,
                    started_at=started_at,
                    finished_at=finished_at,
                    summary="Scheduled task action failed.",
                )
                attach_scheduler_audit(payload, task)
            attach_task_notification(payload, task, event_name(origin, "failed"), origin=origin)
            if scheduler_origin:
                record_scheduler_event(payload)
                payload["events"] = scheduler_events + [scheduler_event_summary(payload)]
                payload["events_path"] = str(scheduler_events_path())
            return payload
        task["run_count"] = int(task.get("run_count") or 0) + 1
        task["last_run_at"] = now_iso()
        task["updated_at"] = task["last_run_at"]
        save_tasks(data)
        append_history(str(task["id"]), f"Executed task `{task['id']}` in local scheduler.")
        payload = {
            "kind": "task-run",
            "status": "ok",
            "ok": True,
            "dry_run": False,
            "task": public_task(task),
            "preview": preview,
            "autonomy_contract": preview["autonomy_contract"],
            "result": action_result,
            "response": action_result.get("response"),
        }
        if scheduler_origin:
            finished_at = now_iso()
            attach_scheduler_metadata(
                payload,
                task,
                event="scheduled_task.completed",
                run_id=run_id,
                scheduled_for=scheduled_for,
                started_at=started_at,
                finished_at=finished_at,
                summary="Scheduled task completed.",
            )
            payload["next_run"] = next_run_for_task(task, finished_at)
            attach_scheduler_audit(payload, task)
        attach_task_notification(payload, task, event_name(origin, "completed"), origin=origin)
        if scheduler_origin:
            record_scheduler_event(payload)
            payload["events"] = scheduler_events + [scheduler_event_summary(payload)]
            payload["events_path"] = str(scheduler_events_path())
        return payload
    except Exception as exc:  # noqa: BLE001 - scheduler runs must isolate task failures.
        if not scheduler_origin:
            raise
        finished_at = now_iso()
        payload = {
            "kind": "task-run",
            "status": "failed",
            "ok": False,
            "dry_run": False,
            "task": public_task(task),
            "preview": preview,
            "autonomy_contract": preview["autonomy_contract"],
            "message": "Scheduled task failed.",
            "reason": "scheduled-task-failed",
            "error": redact_secrets(str(exc)),
            "exit_code": 1,
        }
        attach_scheduler_metadata(
            payload,
            task,
            event="scheduled_task.failed",
            run_id=run_id,
            scheduled_for=scheduled_for,
            started_at=started_at,
            finished_at=finished_at,
            summary="Scheduled task failed.",
        )
        append_history(str(task["id"]), f"Scheduled task `{task['id']}` failed: {exc}")
        attach_scheduler_audit(payload, task)
        attach_task_notification(payload, task, "scheduled_task.failed", origin=origin)
        record_scheduler_event(payload)
        failed_event = scheduler_event_summary(payload)
        retry_event = maybe_schedule_retry_event(task, payload, finished_at, origin=origin)
        payload["events"] = scheduler_events + [failed_event] + ([retry_event] if retry_event else [])
        payload["events_path"] = str(scheduler_events_path())
        return payload


def scheduler_run_once(*, dry_run: bool = False) -> dict[str, Any]:
    data = load_tasks()
    scheduled_for = now_iso()
    due = [item for item in data["tasks"] if isinstance(item, dict) and item.get("status") == "enabled" and task_is_due(item)]
    runs = [run_task(str(item["id"]), dry_run=dry_run, origin="scheduler", run_id=new_run_id(), scheduled_for=scheduled_for) for item in due]
    return {
        "kind": "scheduler",
        "status": "ok",
        "dry_run": dry_run,
        "scheduled_for": scheduled_for,
        "due_count": len(due),
        "runs": runs,
        "events_path": str(scheduler_events_path()),
    }


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


def event_name(origin: str, outcome: str) -> str:
    namespace = "scheduled_task" if origin == "scheduler" else "task"
    return f"{namespace}.{outcome}"


def execute_task_action(task: dict[str, Any], *, origin: str) -> dict[str, Any]:
    action = task.get("action") if isinstance(task.get("action"), dict) else {}
    action_type = str(action.get("type") or "prompt")
    if action_type == "noop":
        return {
            "kind": "task-action",
            "status": "ok",
            "ok": True,
            "message": "No-op local task completed.",
        }
    if action_type == "prompt":
        prompt = str(action.get("prompt") or "").strip()
        if not prompt:
            return {
                "kind": "task-action",
                "status": "failed",
                "ok": False,
                "message": "Task prompt is empty.",
                "exit_code": 2,
            }
        from cli.aikit.core.requests import AgentPromptRequest
        from cli.aikit.natural_prompt_runtime import run_agent_prompt_request

        return run_agent_prompt_request(
            AgentPromptRequest(
                prompt=prompt,
                prog_name="agent",
                project=None,
                new_session=False,
            )
        )
    if action_type == "capability":
        agent_id = str(action.get("agent") or "").strip()
        capability_id = str(action.get("capability") or "").strip()
        if not agent_id or not capability_id:
            return {
                "kind": "task-action",
                "status": "failed",
                "ok": False,
                "message": "Capability task requires agent and capability.",
                "exit_code": 2,
            }
        args = action.get("args") if isinstance(action.get("args"), list) else []
        inputs = action.get("inputs") if isinstance(action.get("inputs"), dict) else {}
        if action.get("external_writes") is True and not args and not inputs:
            return {
                "kind": "task-action",
                "status": "ok",
                "ok": True,
                "agent": agent_id,
                "capability": capability_id,
                "message": "External-write task permission was granted; no capability args were supplied, so no external action was executed.",
                "external_action_executed": False,
            }
        from cli.aikit.capability_runtime import load_agent, run_capability

        return run_capability(load_agent(agent_id), capability_id, [str(item) for item in args], capture_output=True, origin=origin)
    return {
        "kind": "task-action",
        "status": "failed",
        "ok": False,
        "message": f"Unsupported task action type: {action_type}",
        "exit_code": 2,
    }


def new_run_id() -> str:
    return f"run_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"


def scheduler_event_payload(
    task: dict[str, Any],
    *,
    event: str,
    status: str,
    run_id: str | None,
    scheduled_for: str | None,
    started_at: str | None,
    finished_at: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "kind": "scheduled-task-event",
        "event": event,
        "status": status,
        "ok": status in {"ok", "running", "retry_scheduled", "skipped"},
        "task_id": str(task.get("id") or ""),
        "task": public_task(task),
        "run_id": run_id,
        "scheduled_for": scheduled_for,
        "started_at": started_at,
        "summary": summary or f"{event}: {task.get('id') or 'task'}",
        "origin": "scheduler",
        "autonomy_contract": build_task_autonomy_contract(task, origin="scheduler"),
    }
    if finished_at:
        payload["finished_at"] = finished_at
        payload["duration_seconds"] = run_duration_seconds(started_at, finished_at)
    return payload


def attach_scheduler_metadata(
    payload: dict[str, Any],
    task: dict[str, Any],
    *,
    event: str,
    run_id: str | None,
    scheduled_for: str | None,
    started_at: str | None,
    finished_at: str | None,
    summary: str,
) -> None:
    payload["event"] = event
    payload["run_id"] = run_id
    payload["scheduled_for"] = scheduled_for
    payload["started_at"] = started_at
    payload["finished_at"] = finished_at
    payload["summary"] = summary
    payload["origin"] = "scheduler"
    payload["duration_seconds"] = run_duration_seconds(started_at, finished_at)
    payload.setdefault("task_id", str(task.get("id") or ""))


def attach_scheduler_audit(payload: dict[str, Any], task: dict[str, Any]) -> None:
    audit_result = try_record_audit(
        command="scheduler run-task",
        args={
            "task_id": str(task.get("id") or ""),
            "run_id": payload.get("run_id"),
            "event": payload.get("event"),
        },
        result=payload,
        error=payload.get("error") if payload.get("ok") is False else None,
        origin="scheduler",
        required=False,
    )
    audit = audit_result.get("audit")
    if isinstance(audit, dict):
        payload["audit"] = audit
        payload["audit_id"] = audit.get("id")
    warning = audit_result.get("audit_warning")
    if isinstance(warning, dict):
        add_payload_warning(payload, warning)


def record_scheduler_event(payload: dict[str, Any]) -> None:
    event = scheduler_event_summary(payload)
    try:
        with scheduler_events_path().open("a", encoding="utf-8") as file:
            file.write(json.dumps(redact_event_value(event), ensure_ascii=False, sort_keys=True) + "\n")
    except OSError:
        return


def scheduler_event_summary(payload: dict[str, Any]) -> dict[str, Any]:
    notification = payload.get("notification") if isinstance(payload.get("notification"), dict) else {}
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    autonomy_contract = payload.get("autonomy_contract") if isinstance(payload.get("autonomy_contract"), dict) else {}
    return {
        "event": payload.get("event"),
        "status": payload.get("status"),
        "ok": payload.get("ok"),
        "task_id": payload.get("task_id") or (payload.get("task") or {}).get("id"),
        "run_id": payload.get("run_id"),
        "scheduled_for": payload.get("scheduled_for"),
        "started_at": payload.get("started_at"),
        "finished_at": payload.get("finished_at"),
        "duration_seconds": payload.get("duration_seconds"),
        "summary": payload.get("summary") or payload.get("message"),
        "next_run": payload.get("next_run"),
        "audit_id": payload.get("audit_id") or audit.get("id"),
        "notification": {
            "status": notification.get("status"),
            "channel": notification.get("channel"),
            "reason": notification.get("reason"),
        }
        if notification
        else None,
        "autonomy": {
            "level": autonomy_contract.get("level"),
            "level_id": autonomy_contract.get("level_id"),
            "status": autonomy_contract.get("status"),
            "execution_allowed": autonomy_contract.get("execution_allowed"),
        }
        if autonomy_contract
        else None,
    }


def maybe_schedule_retry_event(task: dict[str, Any], failed_payload: dict[str, Any], finished_at: str, *, origin: str) -> dict[str, Any] | None:
    retry = task_retry_config(task)
    if not retry:
        return None
    attempt = int(failed_payload.get("attempt") or 1)
    max_attempts = int(retry.get("max_attempts") or 0)
    if max_attempts <= attempt:
        return None
    delay = parse_interval(str(retry.get("delay") or retry.get("after") or ""))
    finished = parse_iso_datetime(finished_at) or datetime.now(timezone.utc)
    next_run = (finished + delay).isoformat() if delay else None
    retry_event = scheduler_event_payload(
        task,
        event="scheduled_task.retry_scheduled",
        status="retry_scheduled",
        run_id=str(failed_payload.get("run_id") or ""),
        scheduled_for=str(failed_payload.get("scheduled_for") or ""),
        started_at=str(failed_payload.get("started_at") or ""),
        finished_at=finished_at,
        summary=f"Retry scheduled after failure: {failed_payload.get('error') or failed_payload.get('reason') or 'unknown error'}",
    )
    retry_event["attempt"] = attempt + 1
    retry_event["max_attempts"] = max_attempts
    retry_event["next_run"] = next_run
    failed_payload["retry"] = {
        "status": "scheduled",
        "attempt": attempt + 1,
        "max_attempts": max_attempts,
        "next_run": next_run,
    }
    attach_task_notification(retry_event, task, "scheduled_task.retry_scheduled", origin=origin)
    record_scheduler_event(retry_event)
    return scheduler_event_summary(retry_event)


def task_retry_config(task: dict[str, Any]) -> dict[str, Any] | None:
    schedule = task.get("schedule") if isinstance(task.get("schedule"), dict) else {}
    retry = task.get("retry") if isinstance(task.get("retry"), dict) else schedule.get("retry")
    if not isinstance(retry, dict):
        return None
    max_attempts = safe_positive_int(retry.get("max_attempts") or retry.get("max") or retry.get("attempts"))
    if max_attempts is None:
        return None
    return {**retry, "max_attempts": max_attempts}


def next_run_for_task(task: dict[str, Any], finished_at: str) -> str | None:
    schedule = task.get("schedule") if isinstance(task.get("schedule"), dict) else {}
    schedule_type = schedule.get("type") or "manual"
    finished = parse_iso_datetime(finished_at)
    if finished is None:
        return None
    if schedule_type == "interval":
        interval = parse_interval(str(schedule.get("every") or ""))
        return (finished + interval).isoformat() if interval else None
    if schedule_type == "daily":
        scheduled_time = parse_time(str(schedule.get("time") or "00:00")) or time(0, 0)
        candidate = datetime.combine(finished.date(), scheduled_time, tzinfo=timezone.utc)
        if candidate <= finished:
            candidate = candidate + timedelta(days=1)
        return candidate.isoformat()
    return None


def run_duration_seconds(started_at: str | None, finished_at: str | None) -> float | None:
    started = parse_iso_datetime(started_at)
    finished = parse_iso_datetime(finished_at)
    if started is None or finished is None:
        return None
    return round(max(0.0, (finished - started).total_seconds()), 3)


def add_payload_warning(payload: dict[str, Any], warning: dict[str, Any]) -> None:
    warnings = payload.get("warnings")
    if isinstance(warnings, list):
        warnings.append(warning)
    elif warnings:
        payload["warnings"] = [warnings, warning]
    else:
        payload["warnings"] = [warning]


def attach_task_notification(payload: dict[str, Any], task: dict[str, Any], event: str, *, origin: str) -> None:
    try:
        notification = maybe_notify_task(task, event, origin=origin, result=payload)
    except (OSError, ValueError) as exc:
        notification = {
            "kind": "notifications",
            "status": "failed",
            "ok": False,
            "channel": "desktop",
            "reason": "notification-hook-failed",
            "message": redact_secrets(str(exc)),
        }
    if notification is None:
        return
    payload["notification"] = notification
    if notification.get("ok") is False:
        warning = {
            "kind": "notification-warning",
            "message": "Notification was not delivered.",
            "reason": notification.get("reason"),
        }
        add_payload_warning(payload, warning)


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
        "notify": task.get("notify") or {},
        "run_count": int(task.get("run_count") or 0),
        "last_run_at": task.get("last_run_at"),
    }


def task_run_preview(
    task: dict[str, Any],
    *,
    origin: str = "cli",
    dry_run: bool = False,
    permission: dict[str, Any] | None = None,
) -> dict[str, Any]:
    action = task.get("action") if isinstance(task.get("action"), dict) else {}
    autonomy_contract = build_task_autonomy_contract(
        task,
        origin=origin,
        dry_run=dry_run,
        permission=permission,
    )
    return {
        "task_id": task.get("id"),
        "action_type": action.get("type"),
        "agent": action.get("agent"),
        "capability": action.get("capability"),
        "prompt": action.get("prompt"),
        "external_writes": bool(action.get("external_writes")),
        "permissions": task.get("permissions") or {},
        "autonomy_contract": autonomy_contract,
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


def safe_positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


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


def redact_event_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_secrets(value)
    if isinstance(value, list):
        return [redact_event_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): redact_event_value(item) for key, item in value.items()}
    return value
