"""Best-effort local desktop notifications for Agent DevKit."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.aikit.app_home import config_path, ensure_app_home, app_path
from cli.aikit.memory import redact_secrets


SUPPORTED_EVENTS = (
    "task.started",
    "task.completed",
    "task.failed",
    "task.blocked",
    "scheduled_task.started",
    "scheduled_task.progress",
    "scheduled_task.completed",
    "scheduled_task.failed",
    "scheduled_task.blocked",
    "scheduled_task.retry_scheduled",
    "scheduled_task.skipped",
    "automation.completed",
    "automation.failed",
    "wizard.waiting",
    "review.required",
    "provider.missing",
    "artifact.generated",
)
SEVERITIES = {"info", "warning", "error", "action_required"}
DEFAULT_EVENTS = ["task.failed", "task.blocked", "scheduled_task.failed", "scheduled_task.blocked"]
DEFAULT_TITLE = "Agent DevKit"
MAX_TITLE_LENGTH = 80
MAX_MESSAGE_LENGTH = 180
NOTIFICATION_TIMEOUT_SECONDS = 5
LOCAL_CHANNELS = ("desktop", "terminal", "stdout", "audit")
REMOTE_CHANNELS = ("slack", "teams", "whatsapp", "webhook", "mcp-gateway")
CHANNEL_ALIASES = {"local": "desktop", "console": "stdout"}


def terminal_notification(message: str) -> dict[str, Any]:
    return {"type": "terminal", "message": sanitize_message(message)}


def list_notification_events() -> dict[str, Any]:
    return {
        "kind": "notifications",
        "status": "ok",
        "events": list(SUPPORTED_EVENTS),
        "severities": sorted(SEVERITIES),
    }


def list_notification_channels() -> dict[str, Any]:
    return {
        "kind": "notifications",
        "status": "ok",
        "action": "list-channels",
        "channels": [
            {"id": channel, "scope": "local", "status": "supported"}
            for channel in LOCAL_CHANNELS
        ]
        + [
            {"id": channel, "scope": "remote", "status": "future"}
            for channel in REMOTE_CHANNELS
        ],
    }


def notification_doctor() -> dict[str, Any]:
    backend = detect_desktop_backend()
    config = notification_config()
    return {
        "kind": "notifications",
        "status": "ok" if backend["available"] or backend["status"] in {"unsupported", "headless"} else "missing",
        "action": "doctor",
        "desktop": {
            "enabled": config["desktop"]["enabled"],
            "events": config["desktop"]["events"],
            "backend": backend,
        },
        "history_path": str(notification_history_path()),
    }


def configure_notifications(*, enabled: bool | None = None, events: list[str] | None = None) -> dict[str, Any]:
    config = load_app_config()
    notifications = config.setdefault("notifications", {})
    desktop = notifications.setdefault("desktop", {})
    if enabled is not None:
        desktop["enabled"] = bool(enabled)
    if events is not None:
        normalized_events = normalize_events(events)
        desktop["events"] = normalized_events
    desktop.setdefault("enabled", False)
    desktop.setdefault("events", list(DEFAULT_EVENTS))
    channels = notifications.setdefault("channels", {})
    desktop_channel = channels.setdefault("desktop", {})
    desktop_channel["enabled"] = desktop["enabled"]
    desktop_channel["events"] = list(desktop["events"])
    path = save_app_config(config)
    return {
        "kind": "notifications",
        "status": "configured",
        "action": "configure",
        "desktop": notification_config(config)["desktop"],
        "config_path": str(path),
        "stored_secret": False,
    }


def configure_notification_channel(
    channel: str,
    *,
    enabled: bool | None = None,
    events: list[str] | None = None,
) -> dict[str, Any]:
    normalized_channel = normalize_channel(channel)
    if normalized_channel not in LOCAL_CHANNELS:
        return {
            "kind": "notifications",
            "status": "unsupported",
            "ok": False,
            "action": "configure-channel",
            "channel": normalized_channel,
            "reason": "remote-channel-out-of-scope",
        }
    config = load_app_config()
    notifications = config.setdefault("notifications", {})
    channels = notifications.setdefault("channels", {})
    channel_config = channels.setdefault(normalized_channel, {})
    if enabled is not None:
        channel_config["enabled"] = bool(enabled)
    if events is not None:
        channel_config["events"] = normalize_events(events)
    channel_config.setdefault("enabled", False)
    channel_config.setdefault("events", list(DEFAULT_EVENTS))
    if normalized_channel == "desktop":
        desktop = notifications.setdefault("desktop", {})
        desktop["enabled"] = channel_config["enabled"]
        desktop["events"] = list(channel_config["events"])
    path = save_app_config(config)
    return {
        "kind": "notifications",
        "status": "configured",
        "action": "configure-channel",
        "channel": normalized_channel,
        "channel_config": notification_config(config)["channels"][normalized_channel],
        "config_path": str(path),
        "stored_secret": False,
    }


def send_notification_command(
    *,
    title: str = DEFAULT_TITLE,
    message: str,
    event: str = "task.completed",
    severity: str = "info",
    task_id: str | None = None,
    origin: str = "cli",
    status: str | None = None,
    summary: str | None = None,
    artifacts: list[str] | None = None,
    next_steps: list[str] | None = None,
    sensitive: bool = False,
    channels: list[str] | None = None,
) -> dict[str, Any]:
    return send_notification(
        {
            "event": event,
            "title": title,
            "message": message,
            "summary": summary,
            "status": status,
            "severity": severity,
            "task_id": task_id,
            "origin": origin,
            "artifacts": artifacts or [],
            "next_steps": next_steps or [],
            "sensitive": sensitive,
        },
        force=True,
        channels=channels,
    )


def format_notification_event(payload: dict[str, Any]) -> dict[str, Any]:
    event = normalize_event(payload.get("event"))
    severity = normalize_severity(payload.get("severity"))
    summary = sanitize_message(str(payload.get("summary") or payload.get("message") or ""))
    task_id = sanitize_optional(payload.get("task_id"))
    if not summary:
        summary = fallback_message(event, task_id)
    event_payload = {
        "kind": "notification-event",
        "event": event,
        "status": normalize_status(payload.get("status") or status_for_event(event)),
        "task_id": task_id,
        "title": sanitize_title(str(payload.get("title") or DEFAULT_TITLE)),
        "summary": summary,
        "message": summary,
        "artifacts": safe_list(payload.get("artifacts")),
        "next_steps": safe_list(payload.get("next_steps")),
        "severity": severity,
        "sensitive": bool(payload.get("sensitive") is True),
        "origin": normalize_origin(payload.get("origin")),
    }
    for key in ("run_id", "scheduled_for", "started_at", "finished_at", "next_run", "audit_id"):
        value = sanitize_optional(payload.get(key))
        if value is not None:
            event_payload[key] = value
    for key in ("duration_seconds", "attempt", "max_attempts"):
        value = payload.get(key)
        if value is not None:
            event_payload[key] = safe_number(value)
    return event_payload


def send_notification(payload: dict[str, Any], *, force: bool = False, channels: list[str] | None = None) -> dict[str, Any]:
    notification = format_notification_event(payload)
    requested_channels = normalize_channels(channels or payload.get("channels") or ["desktop"])
    deliveries = [send_notification_to_channel(channel, notification, force=force) for channel in requested_channels]
    if len(deliveries) == 1:
        result = deliveries[0]
    else:
        failed = [item for item in deliveries if item.get("ok") is False]
        result = {
            "kind": "notifications",
            "status": "failed" if failed else "sent",
            "ok": not failed,
            "deliveries": deliveries,
            "notification": notification,
        }
    record_notification_attempt(result)
    return result


def send_notification_to_channel(channel: str, notification: dict[str, Any], *, force: bool) -> dict[str, Any]:
    if channel in {"terminal", "stdout", "audit"}:
        return {
            "kind": "notifications",
            "status": "sent",
            "ok": True,
            "channel": channel,
            "notification": notification,
        }
    if channel in REMOTE_CHANNELS:
        return {
            "kind": "notifications",
            "status": "skipped",
            "ok": True,
            "channel": channel,
            "reason": "remote-channel-not-configured",
            "notification": notification,
        }

    config = notification_config()
    if not force and not event_enabled(notification["event"], config, channel=channel):
        return {
            "kind": "notifications",
            "status": "skipped",
            "ok": True,
            "channel": channel,
            "reason": "event-disabled",
            "notification": notification,
        }

    backend = detect_desktop_backend()
    if not backend["available"]:
        return {
            "kind": "notifications",
            "status": "skipped",
            "ok": True,
            "channel": channel,
            "reason": backend["reason"],
            "backend": backend,
            "notification": notification,
        }

    return invoke_backend(backend, notification)


def maybe_notify_task(task: dict[str, Any], event: str, *, origin: str = "cli", result: dict[str, Any] | None = None) -> dict[str, Any] | None:
    channels = task_notification_channels(task, event)
    if not channels and not should_notify_task(task, event):
        return None
    title = str(task.get("title") or task.get("id") or "Task")
    payload = {
        "event": event,
        "title": DEFAULT_TITLE,
        "message": task_event_message(event, task),
        "severity": severity_for_event(event),
        "task_id": str(task.get("id") or ""),
        "origin": origin,
        "artifacts": (result or {}).get("artifacts") or [],
        "next_steps": (result or {}).get("next_steps") or [],
    }
    for key in ("run_id", "scheduled_for", "started_at", "finished_at", "duration_seconds", "next_run", "audit_id", "attempt", "max_attempts"):
        if result and result.get(key) is not None:
            payload[key] = result[key]
    if title and title != payload["task_id"]:
        payload["message"] = f"{payload['message']} ({title})"
    return send_notification(payload, force=bool(channels), channels=channels or None)


def should_notify_task(task: dict[str, Any], event: str) -> bool:
    normalized_event = normalize_event(event)
    if task_notification_channels(task, normalized_event):
        return True
    return event_enabled(normalized_event, notification_config())


def has_explicit_desktop_notification(task: dict[str, Any], event: str) -> bool:
    return "desktop" in task_notification_channels(task, event)


def task_notification_channels(task: dict[str, Any], event: str) -> list[str]:
    normalized_event = normalize_event(event)
    channels: list[str] = []
    notify = task.get("notify") if isinstance(task.get("notify"), dict) else {}
    if notify:
        configured = normalize_task_notification_events(notify.get("on"))
        if normalized_event in configured:
            channels.extend(normalize_channels(notify.get("channels") or ["desktop"]))
    for item in task.get("notifications") or []:
        if not isinstance(item, dict):
            continue
        if item.get("enabled") is False:
            continue
        configured = normalize_task_notification_events(item.get("on"))
        if normalized_event in configured:
            if isinstance(item.get("channels"), list):
                channels.extend(normalize_channels(item.get("channels")))
            else:
                channels.append(normalize_channel(item.get("type") or "desktop"))
    return dedupe(channels)


def normalize_task_notification_events(events: Any) -> set[str]:
    raw_events = events if isinstance(events, list) else ["failed", "blocked", "completed"]
    normalized: set[str] = set()
    for event in raw_events:
        value = str(event or "").strip().lower()
        if value in {"completion", "completed", "success", "ok"}:
            normalized.add("task.completed")
            normalized.add("scheduled_task.completed")
        elif value in {"failure", "failed", "error"}:
            normalized.add("task.failed")
            normalized.add("scheduled_task.failed")
        elif value in {"blocked", "block"}:
            normalized.add("task.blocked")
            normalized.add("scheduled_task.blocked")
        elif value in {"start", "started"}:
            normalized.add("task.started")
            normalized.add("scheduled_task.started")
        elif value in {"progress", "running", "in_progress"}:
            normalized.add("scheduled_task.progress")
        elif value in {"retry", "retry_scheduled", "retry-scheduled"}:
            normalized.add("scheduled_task.retry_scheduled")
        elif value in {"skip", "skipped"}:
            normalized.add("scheduled_task.skipped")
        elif value.startswith("task.") or value.startswith("scheduled_task."):
            normalized.add(normalize_event(value))
    return normalized


def notification_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    if config is None:
        config = load_app_config()
    notifications = config.get("notifications") if isinstance(config.get("notifications"), dict) else {}
    desktop = notifications.get("desktop") if isinstance(notifications.get("desktop"), dict) else {}
    channel_configs = notifications.get("channels") if isinstance(notifications.get("channels"), dict) else {}
    channels: dict[str, dict[str, Any]] = {}
    for channel in LOCAL_CHANNELS:
        raw = channel_configs.get(channel) if isinstance(channel_configs.get(channel), dict) else {}
        if channel == "desktop":
            raw = {**desktop, **raw}
        channels[channel] = {
            "enabled": raw.get("enabled") is True,
            "events": normalize_events(raw.get("events") if isinstance(raw.get("events"), list) else DEFAULT_EVENTS),
        }
    return {
        "desktop": {
            "enabled": channels["desktop"]["enabled"],
            "events": channels["desktop"]["events"],
            "quiet_hours": desktop.get("quiet_hours"),
        },
        "channels": channels,
    }


def load_app_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def save_app_config(config: dict[str, Any]) -> Path:
    ensure_app_home()
    path = config_path()
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def notification_history_path() -> Path:
    ensure_app_home()
    path = app_path("logs", "notifications.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def record_notification_attempt(result: dict[str, Any]) -> None:
    notification = result.get("notification") or {}
    entries: list[dict[str, Any]] = []
    deliveries = result.get("deliveries") if isinstance(result.get("deliveries"), list) else [result]
    for delivery in deliveries:
        if not isinstance(delivery, dict):
            continue
        entries.append(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "event": notification.get("event") or (delivery.get("notification") or {}).get("event"),
                "channel": delivery.get("channel") or "desktop",
                "status": delivery.get("status"),
                "reason": delivery.get("reason"),
                "origin": notification.get("origin") or (delivery.get("notification") or {}).get("origin"),
                "task_id": notification.get("task_id") or (delivery.get("notification") or {}).get("task_id"),
            }
        )
    try:
        with notification_history_path().open("a", encoding="utf-8") as file:
            for entry in entries:
                file.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError:
        return


def detect_desktop_backend() -> dict[str, Any]:
    system = platform.system().lower()
    if system == "darwin":
        command = shutil.which("osascript")
        return {
            "platform": "macos",
            "name": "osascript",
            "available": bool(command),
            "status": "ok" if command else "missing",
            "command": command,
            "reason": None if command else "desktop-notification-unavailable",
        }
    if system == "linux":
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            return {
                "platform": "linux",
                "name": "notify-send",
                "available": False,
                "status": "headless",
                "command": None,
                "reason": "desktop-session-unavailable",
            }
        command = shutil.which("notify-send")
        return {
            "platform": "linux",
            "name": "notify-send",
            "available": bool(command),
            "status": "ok" if command else "missing",
            "command": command,
            "reason": None if command else "desktop-notification-unavailable",
        }
    if system == "windows":
        return {
            "platform": "windows",
            "name": "powershell-toast",
            "available": False,
            "status": "unsupported",
            "command": None,
            "reason": "desktop-notification-unsupported",
            "next_steps": ["Windows toast backend is not enabled in this build; notification attempt will be recorded as skipped."],
        }
    return {
        "platform": system or "unknown",
        "name": None,
        "available": False,
        "status": "unsupported",
        "command": None,
        "reason": "desktop-notification-unsupported",
    }


def invoke_backend(backend: dict[str, Any], notification: dict[str, Any]) -> dict[str, Any]:
    command = backend.get("command")
    if not command:
        return {
            "kind": "notifications",
            "status": "skipped",
            "ok": True,
            "channel": "desktop",
            "reason": "desktop-notification-unavailable",
            "backend": backend,
            "notification": notification,
        }
    if backend.get("platform") == "macos":
        args = [str(command), "-e", f'display notification {json.dumps(notification["message"])} with title {json.dumps(notification["title"])}']
    elif backend.get("platform") == "linux":
        args = [str(command), notification["title"], notification["message"]]
        if notification.get("severity") == "error":
            args.extend(["-u", "critical"])
    else:
        return {
            "kind": "notifications",
            "status": "skipped",
            "ok": True,
            "channel": "desktop",
            "reason": "desktop-notification-unsupported",
            "backend": backend,
            "notification": notification,
        }
    try:
        process = subprocess.run(
            args,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=NOTIFICATION_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "kind": "notifications",
            "status": "failed",
            "ok": False,
            "channel": "desktop",
            "reason": "desktop-notification-failed",
            "message": redact_secrets(str(exc)),
            "backend": backend,
            "notification": notification,
        }
    if process.returncode != 0:
        return {
            "kind": "notifications",
            "status": "failed",
            "ok": False,
            "channel": "desktop",
            "reason": "desktop-notification-failed",
            "returncode": process.returncode,
            "message": sanitize_message(process.stderr or process.stdout or "notification command failed"),
            "backend": backend,
            "notification": notification,
        }
    return {
        "kind": "notifications",
        "status": "sent",
        "ok": True,
        "channel": "desktop",
        "backend": backend,
        "notification": notification,
    }


def event_enabled(event: str, config: dict[str, Any], *, channel: str = "desktop") -> bool:
    channels = config.get("channels") if isinstance(config.get("channels"), dict) else {}
    channel_config = channels.get(channel) if isinstance(channels.get(channel), dict) else None
    if channel_config is None and channel == "desktop":
        channel_config = config.get("desktop") if isinstance(config.get("desktop"), dict) else {}
    return bool(channel_config and channel_config.get("enabled") is True and event in set(channel_config.get("events") or []))


def normalize_events(events: Any) -> list[str]:
    raw = events if isinstance(events, list) else []
    normalized: list[str] = []
    for event in raw:
        value = normalize_event(event)
        if value not in normalized:
            normalized.append(value)
    return normalized or list(DEFAULT_EVENTS)


def normalize_event(event: Any) -> str:
    value = str(event or "").strip().lower()
    if value in SUPPORTED_EVENTS:
        return value
    raise ValueError(f"unsupported notification event: {event}. available: {', '.join(SUPPORTED_EVENTS)}")


def normalize_status(status: Any) -> str:
    value = str(status or "ok").strip().lower()
    allowed = {"ok", "failed", "blocked", "needs-action", "generated", "running", "retry_scheduled", "skipped"}
    if value in allowed:
        return value
    raise ValueError(f"unsupported notification status: {status}. available: {', '.join(sorted(allowed))}")


def normalize_channel(channel: Any) -> str:
    value = str(channel or "desktop").strip().lower()
    value = CHANNEL_ALIASES.get(value, value)
    if value in LOCAL_CHANNELS or value in REMOTE_CHANNELS:
        return value
    raise ValueError(f"unsupported notification channel: {channel}. available: {', '.join(LOCAL_CHANNELS + REMOTE_CHANNELS)}")


def normalize_channels(channels: Any) -> list[str]:
    raw = channels if isinstance(channels, list) else [channels]
    normalized = [normalize_channel(channel) for channel in raw if str(channel or "").strip()]
    return dedupe(normalized) or ["desktop"]


def normalize_severity(severity: Any) -> str:
    value = str(severity or "info").strip().lower()
    if value in SEVERITIES:
        return value
    raise ValueError(f"unsupported notification severity: {severity}. available: {', '.join(sorted(SEVERITIES))}")


def normalize_origin(origin: Any) -> str:
    value = str(origin or "cli").strip().lower()
    allowed = {"cli", "scheduler", "mcp", "wizard", "agent-prompt", "plugin", "core"}
    return value if value in allowed else "cli"


def severity_for_event(event: str) -> str:
    if event.endswith(".failed"):
        return "error"
    if event.endswith(".blocked") or event in {"wizard.waiting", "review.required", "provider.missing"}:
        return "action_required"
    return "info"


def status_for_event(event: str) -> str:
    if event.endswith(".started") or event.endswith(".progress"):
        return "running"
    if event.endswith(".failed"):
        return "failed"
    if event.endswith(".blocked"):
        return "blocked"
    if event.endswith(".retry_scheduled"):
        return "retry_scheduled"
    if event.endswith(".skipped"):
        return "skipped"
    if event in {"wizard.waiting", "review.required", "provider.missing"}:
        return "needs-action"
    if event == "artifact.generated":
        return "generated"
    return "ok"


def task_event_message(event: str, task: dict[str, Any]) -> str:
    task_id = str(task.get("id") or "task")
    if event.endswith(".completed"):
        return f"Tarefa {task_id} concluida."
    if event.endswith(".failed"):
        return f"Tarefa {task_id} falhou."
    if event.endswith(".blocked"):
        return f"Tarefa {task_id} bloqueada."
    if event.endswith(".started"):
        return f"Tarefa {task_id} iniciada."
    if event.endswith(".progress"):
        return f"Tarefa {task_id} em execucao."
    if event.endswith(".retry_scheduled"):
        return f"Retry da tarefa {task_id} agendado."
    if event.endswith(".skipped"):
        return f"Tarefa {task_id} ignorada pelo scheduler."
    return f"Evento {event} em {task_id}."


def fallback_message(event: str, task_id: str | None) -> str:
    target = task_id or "Agent DevKit"
    return f"{event}: {target}"


def sanitize_title(value: str) -> str:
    text = sanitize_message(value, limit=MAX_TITLE_LENGTH)
    return text or DEFAULT_TITLE


def sanitize_message(value: str, *, limit: int = MAX_MESSAGE_LENGTH) -> str:
    text = " ".join(redact_secrets(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def sanitize_optional(value: Any) -> str | None:
    if value is None:
        return None
    text = sanitize_message(str(value), limit=80)
    return text or None


def safe_list(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    return [redact_secrets(str(item)) for item in value[:5]]


def safe_number(value: Any) -> int | float | str:
    if isinstance(value, (int, float)):
        return value
    text = sanitize_message(str(value), limit=40)
    try:
        number = float(text)
    except ValueError:
        return text
    return int(number) if number.is_integer() else number


def dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result
