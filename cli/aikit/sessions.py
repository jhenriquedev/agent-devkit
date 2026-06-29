"""Persistent conversation session helpers for Agent DevKit."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.aikit.app_home import app_path, ensure_app_home, sessions_home
from cli.aikit.autonomy import summarize_autonomy_contract
from cli.aikit.memory import redact_secrets
from cli.aikit.mini_brain import summarize_mini_brain


SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
SESSION_STATE_VERSION = 1
RECENT_CONTEXT_EXCHANGES = 6


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def active_session_path() -> Path:
    return app_path("state", "active-session.json")


def ensure_sessions_home() -> Path:
    ensure_app_home()
    home = sessions_home()
    home.mkdir(parents=True, exist_ok=True)
    return home


def create_session(
    *,
    prompt: str | None = None,
    project: str | None = None,
    backend: str | None = None,
    set_active: bool = True,
) -> dict[str, Any]:
    home = ensure_sessions_home()
    created_at = now_iso()
    session_id = f"sess_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    path = home / session_id
    path.mkdir(parents=True, exist_ok=False)

    state = {
        "version": SESSION_STATE_VERSION,
        "id": session_id,
        "title": title_from_prompt(prompt),
        "status": "active",
        "created_at": created_at,
        "updated_at": created_at,
        "project": project,
        "backend": backend,
        "message_count": 0,
        "exchange_count": 0,
        "token_estimate": 0,
        "path": str(path),
        "summary_path": str(path / "summary.md"),
        "messages_path": str(path / "messages.jsonl"),
    }
    write_state(path, state)
    (path / "messages.jsonl").write_text("", encoding="utf-8")
    write_summary(path, state, latest_prompt=prompt, latest_response=None)
    write_session_markdown(path, state)
    if set_active:
        set_active_session(session_id)
    return public_session(state, active=set_active)


def get_or_create_session(
    *,
    session_id: str | None = None,
    force_new: bool = False,
    prompt: str | None = None,
    project: str | None = None,
    backend: str | None = None,
) -> dict[str, Any]:
    if session_id and force_new:
        raise ValueError("--session and --new-session cannot be used together")
    if session_id:
        state = load_session(session_id)
        set_active_session(state["id"])
        return public_session(state, active=True)
    if force_new:
        return create_session(prompt=prompt, project=project, backend=backend, set_active=True)

    active_id = get_active_session_id()
    if active_id:
        try:
            state = load_session(active_id)
            if project and state.get("project") and state.get("project") != project:
                return create_session(prompt=prompt, project=project, backend=backend, set_active=True)
            if project and not state.get("project"):
                state["project"] = project
                write_state(session_path_from_id(state["id"]), state)
            return public_session(state, active=True)
        except ValueError:
            clear_active_session()
    return create_session(prompt=prompt, project=project, backend=backend, set_active=True)


def list_sessions() -> dict[str, Any]:
    home = ensure_sessions_home()
    active_id = get_active_session_id()
    items: list[dict[str, Any]] = []
    for state_path in sorted(home.glob("*/state.json")):
        try:
            state = read_json(state_path)
        except ValueError:
            continue
        if not isinstance(state, dict):
            continue
        items.append(public_session(state, active=state.get("id") == active_id))
    items.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
    return {
        "kind": "sessions",
        "status": "ok",
        "home": str(home),
        "active_session_id": active_id,
        "items": items,
    }


def show_session(session_id: str) -> dict[str, Any]:
    state = load_session(session_id)
    return {
        "kind": "session",
        "status": "ok",
        "session": public_session(state, active=state["id"] == get_active_session_id()),
        "summary": read_text(Path(state["summary_path"])),
        "recent_messages": recent_exchanges(state["id"], limit=RECENT_CONTEXT_EXCHANGES),
    }


def resume_session(session_id: str) -> dict[str, Any]:
    state = load_session(session_id)
    set_active_session(state["id"])
    return {
        "kind": "session",
        "status": "resumed",
        "session": public_session(state, active=True),
        "summary": read_text(Path(state["summary_path"])),
        "recent_messages": recent_exchanges(state["id"], limit=RECENT_CONTEXT_EXCHANGES),
    }


def record_exchange(
    session_id: str,
    *,
    prompt: str,
    result: dict[str, Any],
    backend: str | None = None,
) -> dict[str, Any]:
    state = load_session(session_id)
    path = session_path_from_id(state["id"])
    response = str(result.get("response") or result.get("message") or "")
    token_delta = estimate_tokens(prompt) + estimate_tokens(response)
    exchange = {
        "type": "exchange",
        "created_at": now_iso(),
        "prompt": redact_secrets(prompt),
        "response": redact_secrets(response),
        "status": result.get("status"),
        "ok": result.get("ok"),
        "backend": result.get("llm_backend") or backend,
        "requires_llm": result.get("requires_llm"),
        "autonomy_contract": summarize_autonomy_contract(result.get("autonomy_contract")),
        "execution_plan": summarize_execution_plan(result.get("execution_plan")),
        "orchestration_trace": result.get("orchestration_trace") or [],
        "token_estimate": token_delta,
    }
    with (path / "messages.jsonl").open("a", encoding="utf-8") as file:
        json.dump(exchange, file, ensure_ascii=False, sort_keys=True)
        file.write("\n")

    state["updated_at"] = exchange["created_at"]
    state["message_count"] = int(state.get("message_count") or 0) + 2
    state["exchange_count"] = int(state.get("exchange_count") or 0) + 1
    state["token_estimate"] = int(state.get("token_estimate") or 0) + token_delta
    if backend and not state.get("backend"):
        state["backend"] = backend
    if state.get("title") == "Untitled session":
        state["title"] = title_from_prompt(prompt)
    write_state(path, state)
    write_summary(path, state, latest_prompt=prompt, latest_response=response)
    write_session_markdown(path, state)
    set_active_session(state["id"])
    return public_session(state, active=True)


def summarize_execution_plan(plan: Any) -> dict[str, Any] | None:
    if not isinstance(plan, dict):
        return None
    return {
        "kind": plan.get("kind"),
        "status": plan.get("status"),
        "coordinator_agent": (plan.get("coordinator_agent") or {}).get("id") if isinstance(plan.get("coordinator_agent"), dict) else None,
        "domain_agent": (plan.get("domain_agent") or {}).get("id") if isinstance(plan.get("domain_agent"), dict) else None,
        "specialist_tasks": [
            {
                "task_id": task.get("task_id") or task.get("id"),
                "agent_id": task.get("agent_id"),
                "capability_id": task.get("capability_id"),
                "role": task.get("role"),
                "depends_on": list(task.get("depends_on") or []),
                "status": task.get("status"),
            }
            for task in plan.get("specialist_tasks") or []
            if isinstance(task, dict)
        ],
        "configuration_tasks": [
            {
                "task_id": task.get("task_id") or task.get("id"),
                "agent_id": task.get("agent_id"),
                "provider": task.get("provider"),
                "role": task.get("role"),
                "depends_on": list(task.get("depends_on") or []),
                "status": task.get("status"),
            }
            for task in plan.get("configuration_tasks") or []
            if isinstance(task, dict)
        ],
        "review_task": {
            "task_id": (plan.get("review_task") or {}).get("task_id") or (plan.get("review_task") or {}).get("id"),
            "agent_id": (plan.get("review_task") or {}).get("agent_id"),
            "role": (plan.get("review_task") or {}).get("role"),
            "depends_on": list((plan.get("review_task") or {}).get("depends_on") or []),
            "status": (plan.get("review_task") or {}).get("status"),
        }
        if isinstance(plan.get("review_task"), dict)
        else None,
        "collaboration_enabled": plan.get("collaboration_enabled") is True,
        "collaboration_graph": summarize_collaboration_graph(plan.get("collaboration_graph")),
        "model_plan": summarize_model_plan(plan.get("model_plan")),
        "execution_model": summarize_execution_model(plan.get("execution_model")),
        "autonomy_contract": summarize_autonomy_contract(plan.get("autonomy_contract")),
        "human_escalations": len(plan.get("human_escalations") or []),
        "shared_context": summarize_shared_context(plan.get("shared_context")),
    }


def summarize_collaboration_graph(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {
        "schema_version": value.get("schema_version"),
        "nodes": len(value.get("nodes") or []),
        "edges": len(value.get("edges") or []),
        "parallel_groups": len(value.get("parallel_groups") or []),
    }


def summarize_shared_context(value: Any) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    return {
        key: len(value.get(key) or [])
        for key in (
            "facts",
            "inferences",
            "artifacts",
            "blockers",
            "decisions",
            "risks",
            "questions",
            "handoffs",
            "conflicts",
            "human_escalations",
        )
    }


def summarize_execution_model(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {
        "schema_version": value.get("schema_version"),
        "decision_owner": value.get("decision_owner"),
        "review_required": value.get("review_required"),
        "model_strategy": value.get("model_strategy"),
        "model_risk": value.get("model_risk"),
        "model_confidence": value.get("model_confidence"),
        "autonomy_level": value.get("autonomy_level"),
        "autonomy_level_id": value.get("autonomy_level_id"),
        "autonomy_status": value.get("autonomy_status"),
        "execution_allowed": value.get("execution_allowed"),
        "requires_human": value.get("requires_human"),
        "limits": value.get("limits") if isinstance(value.get("limits"), dict) else {},
        "stop_conditions": list(value.get("stop_conditions") or []),
    }


def summarize_model_plan(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {
        "strategy": value.get("strategy"),
        "risk": value.get("risk"),
        "confidence": value.get("confidence"),
        "fallback": value.get("fallback"),
        "local_llm_selected": value.get("local_llm_selected") is True,
        "local_llm_recommended": value.get("local_llm_recommended") is True,
        "mini_brain": summarize_mini_brain(value.get("mini_brain")),
        "max_llm_calls": value.get("max_llm_calls"),
    }


def build_contextual_prompt(session_id: str, prompt: str) -> str:
    exchanges = recent_exchanges(session_id, limit=RECENT_CONTEXT_EXCHANGES)
    safe_prompt = redact_secrets(prompt)
    if not exchanges:
        return safe_prompt
    lines = [
        "Contexto recente da sessao atual do Agent DevKit:",
    ]
    for item in exchanges:
        previous_prompt = compact_line(str(item.get("prompt") or ""))
        previous_response = compact_line(str(item.get("response") or ""))
        if previous_prompt:
            lines.append(f"- Usuario: {previous_prompt}")
        if previous_response:
            lines.append(f"  Assistente: {previous_response}")
    lines.extend(["", "Pedido atual do usuario:", safe_prompt])
    return "\n".join(lines)


def load_session(session_id: str) -> dict[str, Any]:
    resolved_id = resolve_session_id(session_id)
    path = session_path_from_id(resolved_id)
    state_path = path / "state.json"
    if not state_path.exists():
        raise ValueError(f"session not found: {session_id}")
    state = read_json(state_path)
    if not isinstance(state, dict):
        raise ValueError(f"invalid session state: {session_id}")
    state.setdefault("id", resolved_id)
    state.setdefault("path", str(path))
    state.setdefault("summary_path", str(path / "summary.md"))
    state.setdefault("messages_path", str(path / "messages.jsonl"))
    return state


def resolve_session_id(session_id: str) -> str:
    if not session_id:
        raise ValueError("session id is required")
    if not SESSION_ID_PATTERN.match(session_id):
        raise ValueError(f"invalid session id: {session_id}")
    home = ensure_sessions_home()
    direct = home / session_id
    if direct.exists():
        return session_id
    matches = [path.name for path in home.iterdir() if path.is_dir() and path.name.startswith(session_id)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f"ambiguous session id prefix: {session_id}")
    raise ValueError(f"session not found: {session_id}")


def session_path_from_id(session_id: str) -> Path:
    return ensure_sessions_home() / session_id


def set_active_session(session_id: str) -> None:
    ensure_app_home()
    path = active_session_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": SESSION_STATE_VERSION, "session_id": session_id, "updated_at": now_iso()}
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def get_active_session_id() -> str | None:
    path = active_session_path()
    if not path.exists():
        return None
    try:
        data = read_json(path)
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    session_id = data.get("session_id")
    if not isinstance(session_id, str) or not SESSION_ID_PATTERN.match(session_id):
        return None
    if not (sessions_home() / session_id / "state.json").exists():
        return None
    return session_id


def clear_active_session() -> None:
    path = active_session_path()
    if path.exists():
        path.unlink()


def public_session(state: dict[str, Any], *, active: bool = False) -> dict[str, Any]:
    return {
        "id": state.get("id"),
        "title": state.get("title") or "Untitled session",
        "status": state.get("status") or "active",
        "created_at": state.get("created_at"),
        "updated_at": state.get("updated_at"),
        "project": state.get("project"),
        "backend": state.get("backend"),
        "message_count": int(state.get("message_count") or 0),
        "exchange_count": int(state.get("exchange_count") or 0),
        "token_estimate": int(state.get("token_estimate") or 0),
        "path": state.get("path"),
        "active": active,
    }


def recent_exchanges(session_id: str, *, limit: int) -> list[dict[str, Any]]:
    path = session_path_from_id(resolve_session_id(session_id)) / "messages.jsonl"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            items.append(item)
    return items[-limit:]


def title_from_prompt(prompt: str | None) -> str:
    if not prompt:
        return "Untitled session"
    text = compact_line(redact_secrets(prompt))
    words = text.split()
    if not words:
        return "Untitled session"
    title = " ".join(words[:8])
    return title[:80]


def estimate_tokens(text: str | None) -> int:
    if not text:
        return 0
    compact = " ".join(str(text).split())
    return max(1, (len(compact) + 3) // 4)


def compact_line(value: str, *, limit: int = 600) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def write_state(path: Path, state: dict[str, Any]) -> None:
    with (path / "state.json").open("w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")


def write_summary(path: Path, state: dict[str, Any], *, latest_prompt: str | None, latest_response: str | None) -> None:
    lines = [
        f"# {state.get('title') or 'Untitled session'}",
        "",
        f"- Session: {state.get('id')}",
        f"- Status: {state.get('status') or 'active'}",
        f"- Created: {state.get('created_at') or '-'}",
        f"- Updated: {state.get('updated_at') or '-'}",
        f"- Project: {state.get('project') or '-'}",
        f"- Backend: {state.get('backend') or '-'}",
        f"- Exchanges: {state.get('exchange_count') or 0}",
        f"- Token estimate: {state.get('token_estimate') or 0}",
        "",
        "## Latest",
        "",
        f"- Prompt: {compact_line(redact_secrets(latest_prompt or '-'))}",
        f"- Response: {compact_line(redact_secrets(latest_response or '-'))}",
        "",
    ]
    (path / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_session_markdown(path: Path, state: dict[str, Any]) -> None:
    lines = [
        f"# {state.get('title') or 'Untitled session'}",
        "",
        "This folder stores a local Agent DevKit conversation session.",
        "",
        "## Files",
        "",
        "- `state.json`: machine-readable metadata.",
        "- `summary.md`: human-readable rolling summary.",
        "- `messages.jsonl`: append-only redacted exchanges.",
        "",
    ]
    (path / "session.md").write_text("\n".join(lines), encoding="utf-8")


def read_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON file: {path}") from exc


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""
