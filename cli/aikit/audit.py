"""Local audit trail for Agent DevKit CLI executions."""

from __future__ import annotations

import getpass
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.aikit.app_home import audit_home, ensure_app_home
from cli.aikit.memory import normalize_prompt, redact_secrets


AUDIT_VERSION = 1


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


def ensure_audit_home() -> Path:
    ensure_app_home()
    home = audit_home()
    home.mkdir(parents=True, exist_ok=True)
    return home


def audit_day_home(day: str | None = None) -> Path:
    resolved_day = day or now_utc().date().isoformat()
    path = ensure_audit_home() / resolved_day
    path.mkdir(parents=True, exist_ok=True)
    return path


def record_audit(
    *,
    command: str | None,
    args: dict[str, Any],
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    created_at = now_iso()
    execution_id = f"exec_{now_utc().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    prompt = extract_prompt(args)
    safe_result = redact_value(result or {})
    entry = {
        "version": AUDIT_VERSION,
        "id": execution_id,
        "created_at": created_at,
        "user": safe_user(),
        "command": command,
        "prompt": redact_secrets(prompt) if prompt else None,
        "prompt_normalized": normalize_prompt(prompt) if prompt else None,
        "session": extract_session(safe_result),
        "route": safe_result.get("route"),
        "orchestration": extract_orchestration(safe_result),
        "agent": extract_agent(safe_result, args),
        "providers": extract_providers(safe_result),
        "sources": extract_sources(safe_result),
        "commands": extract_commands(safe_result),
        "permissions": extract_permissions(safe_result),
        "llm_backends": extract_llm_backends(safe_result),
        "token_estimate": extract_token_estimate(safe_result),
        "external_actions": extract_external_actions(safe_result),
        "result": summarize_result(safe_result),
        "error": redact_secrets(error) if error else None,
        "redaction_applied": True,
    }
    day_home = audit_day_home(created_at[:10])
    json_path = day_home / f"{execution_id}.json"
    md_path = day_home / f"{execution_id}.md"
    json_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_audit_md(entry), encoding="utf-8")
    return {"id": execution_id, "json_path": str(json_path), "markdown_path": str(md_path)}


def list_audits(limit: int = 20) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for path in sorted(ensure_audit_home().glob("*/*.json"), reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        items.append(
            {
                "id": payload.get("id"),
                "created_at": payload.get("created_at"),
                "command": payload.get("command"),
                "status": (payload.get("result") or {}).get("status"),
                "ok": (payload.get("result") or {}).get("ok"),
                "json_path": str(path),
                "markdown_path": str(path.with_suffix(".md")),
            }
        )
        if len(items) >= limit:
            break
    return {"kind": "audit", "status": "ok", "home": str(ensure_audit_home()), "items": items}


def show_audit(execution_id: str) -> dict[str, Any]:
    path = find_audit_json(execution_id)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "kind": "audit-entry",
        "status": "ok",
        "id": payload.get("id"),
        "entry": payload,
        "json_path": str(path),
        "markdown_path": str(path.with_suffix(".md")),
    }


def export_audit(execution_id: str, *, fmt: str = "md") -> dict[str, Any]:
    path = find_audit_json(execution_id)
    if fmt == "json":
        content = path.read_text(encoding="utf-8")
        export_path = path
    elif fmt == "md":
        md_path = path.with_suffix(".md")
        content = md_path.read_text(encoding="utf-8") if md_path.exists() else render_audit_md(json.loads(path.read_text(encoding="utf-8")))
        export_path = md_path
    else:
        raise ValueError("--format must be md or json")
    return {
        "kind": "audit-export",
        "status": "ok",
        "id": execution_id,
        "format": fmt,
        "path": str(export_path),
        "content": content,
    }


def find_audit_json(execution_id: str) -> Path:
    if not execution_id or "/" in execution_id or "\\" in execution_id:
        raise ValueError(f"invalid audit execution id: {execution_id}")
    matches = sorted(ensure_audit_home().glob(f"*/{execution_id}.json"))
    if not matches:
        prefix_matches = sorted(ensure_audit_home().glob(f"*/{execution_id}*.json"))
        if len(prefix_matches) == 1:
            return prefix_matches[0]
        if len(prefix_matches) > 1:
            raise ValueError(f"ambiguous audit execution id prefix: {execution_id}")
        raise ValueError(f"audit execution not found: {execution_id}")
    return matches[0]


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_secrets(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if secret_key(key_text):
                redacted[key_text] = "[REDACTED_SECRET]"
            else:
                redacted[key_text] = redact_value(item)
        return redacted
    return value


def secret_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    if normalized in {"token_estimate", "tokens", "prompt_tokens", "completion_tokens", "total_tokens"}:
        return False
    exact = {"token", "secret", "password", "passwd", "pwd", "api_key", "private_key", "pat"}
    if normalized in exact:
        return True
    if normalized.endswith(("_token", "_secret", "_password", "_passwd", "_pwd", "_api_key", "_private_key", "_pat")):
        return True
    compact = re.sub(r"[^a-z0-9]+", "", key.lower())
    if compact in {"tokenestimate", "tokens", "prompttokens", "completiontokens", "totaltokens"}:
        return False
    return any(marker in compact for marker in ("token", "secret", "password", "passwd", "apikey", "privatekey"))


def extract_prompt(args: dict[str, Any]) -> str | None:
    prompt = args.get("prompt")
    if isinstance(prompt, list):
        return " ".join(str(item) for item in prompt).strip()
    return str(prompt).strip() if prompt else None


def extract_session(result: dict[str, Any]) -> dict[str, Any] | None:
    session = result.get("session")
    if isinstance(session, dict):
        return {
            "id": session.get("id"),
            "title": session.get("title"),
            "project": session.get("project"),
            "token_estimate": session.get("token_estimate"),
        }
    return None


def extract_agent(result: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    if isinstance(result.get("agent"), dict):
        return result["agent"]
    if result.get("agent_id"):
        return {"id": result.get("agent_id")}
    if args.get("agent"):
        return {"id": args.get("agent")}
    route = result.get("route") if isinstance(result.get("route"), dict) else {}
    if route.get("agent_id"):
        return {"id": route.get("agent_id"), "capability": route.get("capability_id")}
    return {}


def extract_providers(result: dict[str, Any]) -> Any:
    if result.get("providers") is not None:
        return result.get("providers")
    route = result.get("route") if isinstance(result.get("route"), dict) else {}
    provider = result.get("provider") or route.get("provider") or result.get("source_provider")
    return {"used": [provider], "missing": [], "skipped": []} if provider else {"used": [], "missing": [], "skipped": []}


def extract_sources(result: dict[str, Any]) -> list[Any]:
    source = result.get("source")
    if source:
        return [source]
    return []


def extract_commands(result: dict[str, Any]) -> list[Any]:
    commands = []
    command = result.get("command")
    if command:
        commands.append(command)
    for attempt in result.get("llm_backend_attempts") or []:
        if isinstance(attempt, dict) and attempt.get("command"):
            commands.append(attempt["command"])
    return commands


def extract_permissions(result: dict[str, Any]) -> list[Any]:
    permissions = []
    for key in ("permission", "permissions"):
        if result.get(key):
            permissions.append(result[key])
    preview = result.get("preview") if isinstance(result.get("preview"), dict) else {}
    if preview.get("permissions"):
        permissions.append(preview["permissions"])
    return permissions


def extract_llm_backends(result: dict[str, Any]) -> list[Any]:
    attempts = result.get("llm_backend_attempts")
    if isinstance(attempts, list):
        return attempts
    backend = result.get("llm_backend")
    return [{"id": backend}] if backend else []


def extract_token_estimate(result: dict[str, Any]) -> int | None:
    session = result.get("session") if isinstance(result.get("session"), dict) else {}
    if session.get("token_estimate") is not None:
        return int(session.get("token_estimate") or 0)
    prompt_length = result.get("prompt_length")
    return int(prompt_length / 4) if isinstance(prompt_length, int) else None


def extract_external_actions(result: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    preview = result.get("preview") if isinstance(result.get("preview"), dict) else {}
    if preview.get("external_writes"):
        actions.append({"type": preview.get("action_type"), "external_writes": True})
    if result.get("external_action"):
        actions.append(result["external_action"])
    return actions


def extract_orchestration(result: dict[str, Any]) -> dict[str, Any] | None:
    plan = result.get("execution_plan")
    if not isinstance(plan, dict):
        return None
    return {
        "kind": plan.get("kind"),
        "status": plan.get("status"),
        "coordinator_agent": (plan.get("coordinator_agent") or {}).get("id") if isinstance(plan.get("coordinator_agent"), dict) else None,
        "domain_agent": (plan.get("domain_agent") or {}).get("id") if isinstance(plan.get("domain_agent"), dict) else None,
        "specialist_tasks": [
            {
                "agent_id": task.get("agent_id"),
                "capability_id": task.get("capability_id"),
                "status": task.get("status"),
            }
            for task in plan.get("specialist_tasks") or []
            if isinstance(task, dict)
        ],
        "configuration_tasks": [
            {
                "agent_id": task.get("agent_id"),
                "provider": task.get("provider"),
                "status": task.get("status"),
            }
            for task in plan.get("configuration_tasks") or []
            if isinstance(task, dict)
        ],
        "review_task": {
            "agent_id": (plan.get("review_task") or {}).get("agent_id"),
            "status": (plan.get("review_task") or {}).get("status"),
        }
        if isinstance(plan.get("review_task"), dict)
        else None,
        "trace": result.get("orchestration_trace") or plan.get("trace") or [],
    }


def summarize_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": result.get("kind"),
        "status": result.get("status"),
        "ok": result.get("ok"),
        "exit_code": result.get("exit_code"),
        "message": result.get("message"),
        "mode": result.get("mode"),
    }


def safe_user() -> str:
    try:
        return redact_secrets(getpass.getuser())
    except Exception:
        return "unknown"


def render_audit_md(entry: dict[str, Any]) -> str:
    lines = [
        f"# Audit {entry.get('id')}",
        "",
        f"- Created at: `{entry.get('created_at')}`",
        f"- User: `{entry.get('user')}`",
        f"- Command: `{entry.get('command')}`",
        f"- Status: `{(entry.get('result') or {}).get('status')}`",
        f"- OK: `{(entry.get('result') or {}).get('ok')}`",
        "",
        "## Prompt",
        "",
        entry.get("prompt") or "-",
        "",
        "## Agent",
        "",
        "```json",
        json.dumps(entry.get("agent") or {}, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Providers",
        "",
        "```json",
        json.dumps(entry.get("providers") or {}, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Orchestration",
        "",
        "```json",
        json.dumps(entry.get("orchestration") or {}, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Permissions",
        "",
        "```json",
        json.dumps(entry.get("permissions") or [], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Result",
        "",
        "```json",
        json.dumps(entry.get("result") or {}, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    if entry.get("error"):
        lines.extend(["", "## Error", "", str(entry["error"])])
    lines.append("")
    return "\n".join(lines)
