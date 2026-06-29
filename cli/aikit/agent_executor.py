"""Execution helpers for multi-agent plans."""

from __future__ import annotations

from typing import Any, Callable

from cli.aikit.write_policy import (
    is_autonomous_safe_write_policy,
    normalize_write_policy,
    write_policy_public_fields,
)


RunCapability = Callable[[dict[str, Any], str, list[str]], dict[str, Any]]
LoadAgent = Callable[[str], dict[str, Any]]


def execute_plan_tasks(
    plan: dict[str, Any],
    *,
    load_agent: LoadAgent,
    run_capability: RunCapability,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    executed: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for task in plan.get("specialist_tasks") or []:
        if not task.get("primary"):
            continue
        if not task.get("executable"):
            blocked.append(blocked_task(task, "Capability has no executable runner."))
            continue
        if not is_autonomous_safe_write_policy(task.get("write_policy")):
            blocked.append(blocked_task(task, "Capability requires explicit confirmation for external write effects."))
            continue
        try:
            agent = load_agent(str(task["agent_id"]))
            result = run_capability(agent, str(task["capability_id"]), list(task.get("args") or []))
        except Exception as exc:  # pragma: no cover - converted to user-facing payload.
            blocked.append(blocked_task(task, str(exc)))
            continue
        item = public_task_result(task, result)
        if result.get("ok"):
            executed.append(item)
        else:
            blocked.append(item)
    return executed, blocked


def public_task_result(task: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": task.get("id"),
        "task_id": task.get("task_id") or task.get("id"),
        "agent_id": task.get("agent_id"),
        "capability_id": task.get("capability_id"),
        "role": task.get("role"),
        "depends_on": list(task.get("depends_on") or []),
        "handoff": task.get("handoff") if isinstance(task.get("handoff"), dict) else {},
        "status": result.get("status"),
        "ok": bool(result.get("ok")),
        "provider": task.get("provider"),
        "write_policy": normalize_write_policy(task.get("write_policy")),
        "write_policy_metadata": task_write_policy_metadata(task),
        "result": result,
    }


def blocked_task(task: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "id": task.get("id"),
        "task_id": task.get("task_id") or task.get("id"),
        "agent_id": task.get("agent_id"),
        "capability_id": task.get("capability_id"),
        "role": task.get("role"),
        "depends_on": list(task.get("depends_on") or []),
        "handoff": task.get("handoff") if isinstance(task.get("handoff"), dict) else {},
        "status": "blocked",
        "ok": False,
        "provider": task.get("provider"),
        "write_policy": normalize_write_policy(task.get("write_policy")),
        "write_policy_metadata": task_write_policy_metadata(task),
        "reason": reason,
    }


def task_write_policy_metadata(task: dict[str, Any]) -> dict[str, Any]:
    metadata = task.get("write_policy_metadata")
    if isinstance(metadata, dict):
        return metadata
    return write_policy_public_fields(task.get("write_policy"))["write_policy_metadata"]
