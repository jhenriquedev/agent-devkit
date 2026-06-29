"""Controlled execution loop for declared live module modes."""

from __future__ import annotations

from typing import Any, Callable

from cli.aikit.agent_executor import blocked_task, public_task_result
from cli.aikit.audit import try_record_audit
from cli.aikit.collaboration import (
    blocked_dependency,
    collaborative_task_sequence,
    merge_task_handoff,
    normalize_shared_context,
)
from cli.aikit.write_policy import is_autonomous_safe_write_policy


RunCapability = Callable[[dict[str, Any], str, list[str]], dict[str, Any]]
LoadAgent = Callable[[str], dict[str, Any]]


def run_module_controller(
    plan: dict[str, Any],
    *,
    load_agent: LoadAgent,
    run_capability: RunCapability,
    max_steps: int | None = None,
) -> dict[str, Any]:
    agent = plan.get("domain_agent") if isinstance(plan.get("domain_agent"), dict) else {}
    mode = agent.get("agent_mode") if isinstance(agent.get("agent_mode"), dict) else {}
    if not mode:
        return controller_payload(
            status="not-enabled",
            agent_id=str(agent.get("id") or ""),
            mode={},
            steps=[],
            stop_reason="agent-mode-not-declared",
        )
    limit = bounded_steps(max_steps or mode.get("max_steps") or 1)
    specialist_limit = bounded_steps(mode.get("max_specialists") or limit)
    limit = min(limit, specialist_limit)
    allowed = allowed_capabilities(mode)
    if mode.get("can_call_capabilities") is not True:
        return controller_payload(
            status="blocked",
            agent_id=str(agent.get("id") or ""),
            mode=mode,
            steps=[],
            stop_reason="capability-calls-disabled",
            autonomy_contract=plan.get("autonomy_contract") if isinstance(plan.get("autonomy_contract"), dict) else None,
        )
    autonomy_contract = plan.get("autonomy_contract") if isinstance(plan.get("autonomy_contract"), dict) else {}
    if autonomy_contract and autonomy_contract.get("execution_allowed") is not True:
        return controller_payload(
            status="needs-input" if autonomy_contract.get("requires_human") else "blocked",
            agent_id=str(agent.get("id") or ""),
            mode=mode,
            steps=[],
            stop_reason=str(autonomy_contract.get("status") or "autonomy-blocked"),
            autonomy_contract=autonomy_contract,
            human_escalations=[
                {
                    "source": "autonomy-contract",
                    "kind": "autonomy-required-input",
                    "reason": "; ".join(str(item) for item in autonomy_contract.get("blockers") or []),
                    "confidence": "high",
                    "status": "waiting-for-user",
                }
            ]
            if autonomy_contract.get("requires_human")
            else [],
        )
    collaboration_enabled = plan.get("collaboration_enabled") is True
    tasks = collaborative_task_sequence(plan)
    if not tasks:
        status = "needs-input" if mode.get("can_request_user_input") else "blocked"
        return controller_payload(
            status=status,
            agent_id=str(agent.get("id") or ""),
            mode=mode,
            steps=[],
            stop_reason="no-primary-task",
            autonomy_contract=autonomy_contract or None,
        )

    steps: list[dict[str, Any]] = []
    executed: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    completed_task_ids: set[str] = set()
    failed_task_ids: set[str] = set()
    shared_context = normalize_shared_context(plan.get("shared_context"))
    stop_reason = "max-steps"
    processed = 0
    for task in tasks[:limit]:
        processed += 1
        step = controller_step(task, index=len(steps) + 1)
        block_reason = None
        if collaboration_enabled:
            block_reason = blocked_dependency(task, completed_task_ids, failed_task_ids)
        block_reason = block_reason or task_block_reason(task, allowed=allowed)
        if block_reason:
            blocked_item = blocked_task(task, block_reason)
            blocked.append(blocked_item)
            failed_task_ids.add(str(task.get("task_id") or task.get("id")))
            step["status"] = "blocked"
            step["observation"] = {"ok": False, "reason": block_reason}
            step["review"] = {"status": "blocked", "reason": block_reason}
            shared_context = merge_task_handoff(
                shared_context,
                task,
                {"ok": False, "status": "blocked", "reason": block_reason},
            )
            step["shared_context"] = context_counts(shared_context)
            attach_step_audit(step, result=blocked_item)
            steps.append(step)
            stop_reason = "blocked"
            break
        try:
            loaded_agent = load_agent(str(task["agent_id"]))
            result = run_capability(loaded_agent, str(task["capability_id"]), list(task.get("args") or []))
        except Exception as exc:  # noqa: BLE001 - controller must convert failures to structured results.
            blocked_item = blocked_task(task, str(exc))
            blocked.append(blocked_item)
            failed_task_ids.add(str(task.get("task_id") or task.get("id")))
            step["status"] = "blocked"
            step["observation"] = {"ok": False, "reason": str(exc)}
            step["review"] = {"status": "blocked", "reason": str(exc)}
            shared_context = merge_task_handoff(
                shared_context,
                task,
                {"ok": False, "status": "blocked", "reason": str(exc)},
            )
            step["shared_context"] = context_counts(shared_context)
            attach_step_audit(step, result=blocked_item)
            steps.append(step)
            stop_reason = "blocked"
            break
        item = public_task_result(task, result)
        step["status"] = item["status"]
        step["observation"] = observe_result(result)
        step["review"] = review_observation(step["observation"])
        shared_context = merge_task_handoff(shared_context, task, result)
        step["shared_context"] = context_counts(shared_context)
        attach_step_audit(step, result=item)
        steps.append(step)
        if result.get("ok"):
            executed.append(item)
            completed_task_ids.add(str(task.get("task_id") or task.get("id")))
            stop_reason = "success" if processed >= len(tasks) else "max-steps"
            if not collaboration_enabled and "success" in set(mode.get("stop_conditions") or []):
                break
            continue
        blocked.append(item)
        failed_task_ids.add(str(task.get("task_id") or task.get("id")))
        stop_reason = "needs-input" if result.get("status") == "needs-input" else "blocked"
        break

    if collaboration_enabled and executed and not blocked and processed >= min(len(tasks), limit):
        stop_reason = "success" if processed >= len(tasks) else "max-steps"
    if collaboration_enabled and not blocked and len(tasks) > limit:
        stop_reason = "max-specialists"
        shared_context["human_escalations"].append(
            {
                "source": str(agent.get("id") or "module-controller"),
                "kind": "max-specialists",
                "reason": "Specialist execution limit was reached before all planned tasks completed.",
                "confidence": "medium",
                "status": "waiting-for-user",
            }
        )
    if collaboration_enabled and shared_context.get("human_escalations") and stop_reason in {"blocked", "max-specialists"}:
        stop_reason = "needs-input"

    status = controller_status(executed, blocked, stop_reason=stop_reason, steps=steps)
    return controller_payload(
        status=status,
        agent_id=str(agent.get("id") or ""),
        mode=mode,
        steps=steps,
        stop_reason=stop_reason,
        executed=executed,
        blocked=blocked,
        shared_context=shared_context,
        human_escalations=list(shared_context.get("human_escalations") or []),
        autonomy_contract=autonomy_contract or None,
    )


def controller_payload(
    *,
    status: str,
    agent_id: str,
    mode: dict[str, Any],
    steps: list[dict[str, Any]],
    stop_reason: str,
    executed: list[dict[str, Any]] | None = None,
    blocked: list[dict[str, Any]] | None = None,
    shared_context: dict[str, Any] | None = None,
    human_escalations: list[dict[str, Any]] | None = None,
    autonomy_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "kind": "module-controller-run",
        "status": status,
        "ok": status == "ok",
        "agent_id": agent_id,
        "mode": mode,
        "steps": steps,
        "observations": [step.get("observation") for step in steps if isinstance(step.get("observation"), dict)],
        "review": steps[-1].get("review") if steps else {},
        "stop_reason": stop_reason,
        "executed_tasks": executed or [],
        "blocked_tasks": blocked or [],
        "shared_context": normalize_shared_context(shared_context),
        "human_escalations": human_escalations or [],
    }
    if autonomy_contract:
        payload["autonomy_contract"] = autonomy_contract
    return payload


def controller_step(task: dict[str, Any], *, index: int) -> dict[str, Any]:
    return {
        "index": index,
        "phase": "act",
        "task_id": task.get("task_id") or task.get("id"),
        "agent_id": task.get("agent_id"),
        "capability_id": task.get("capability_id"),
        "role": task.get("role"),
        "depends_on": list(task.get("depends_on") or []),
        "status": "planned",
    }


def task_block_reason(task: dict[str, Any], *, allowed: set[str]) -> str | None:
    pair = f"{task.get('agent_id')}/{task.get('capability_id')}"
    if allowed and pair not in allowed:
        return "Capability is not allowed by agent_mode.allowed_capabilities."
    if not task.get("executable"):
        return "Capability has no executable runner."
    if not is_autonomous_safe_write_policy(task.get("write_policy")):
        return "Capability requires explicit confirmation for external write effects."
    return None


def observe_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(result.get("ok")),
        "status": result.get("status"),
        "reason": result.get("reason"),
        "risks": list(result.get("risks") or []),
        "next_steps": list(result.get("next_steps") or []),
    }


def review_observation(observation: dict[str, Any]) -> dict[str, Any]:
    if observation.get("ok"):
        return {"status": "accepted", "reason": "result-ok"}
    if observation.get("status") == "needs-input":
        return {"status": "needs-input", "reason": observation.get("reason") or "missing-input"}
    return {"status": "blocked", "reason": observation.get("reason") or "result-not-ok"}


def context_counts(shared_context: dict[str, Any]) -> dict[str, int]:
    return {
        key: len(shared_context.get(key) or [])
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


def attach_step_audit(step: dict[str, Any], *, result: dict[str, Any]) -> None:
    audit_result = try_record_audit(
        command="module-controller step",
        args={
            "agent_id": step.get("agent_id"),
            "capability_id": step.get("capability_id"),
            "step": step.get("index"),
        },
        result=result,
        error=result.get("reason") if result.get("ok") is False else None,
        origin="core",
        required=False,
    )
    audit = audit_result.get("audit")
    if isinstance(audit, dict):
        step["audit"] = audit
        step["audit_id"] = audit.get("id")
    warning = audit_result.get("audit_warning")
    if isinstance(warning, dict):
        step["audit_warning"] = warning


def allowed_capabilities(mode: dict[str, Any]) -> set[str]:
    return {str(item) for item in mode.get("allowed_capabilities") or [] if "/" in str(item)}


def bounded_steps(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 1
    return min(max(parsed, 1), 20)


def controller_status(
    executed: list[dict[str, Any]],
    blocked: list[dict[str, Any]],
    *,
    stop_reason: str,
    steps: list[dict[str, Any]],
) -> str:
    if stop_reason == "needs-input":
        return "needs-input"
    if stop_reason == "max-specialists":
        return "needs-input"
    if blocked and not executed:
        return "blocked"
    if blocked and executed:
        return "partial"
    if executed:
        return "ok"
    if steps:
        return "limit-reached"
    return "blocked"
