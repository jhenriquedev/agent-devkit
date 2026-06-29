"""Controlled autonomy contracts for Agent DevKit plans and tasks."""

from __future__ import annotations

from typing import Any


AUTONOMY_SCHEMA_VERSION = "ai-devkit.autonomy/v1"


LEVELS = {
    0: ("manual", "User runs commands or capabilities directly."),
    1: ("assisted", "Agent DevKit suggests, asks, or delegates reasoning before execution."),
    2: ("deterministic", "Known read-only or dry-run capabilities can execute without external LLM."),
    3: ("supervised", "Side-effecting work requires explicit human confirmation."),
    4: ("scheduled", "Recurring local tasks execute with limits, audit, and notifications."),
    5: ("collaborative", "Multiple specialist agents are coordinated by the runtime."),
    6: ("controlled-autonomy", "Composed workflows execute inside policy, budget, audit, and stop conditions."),
}


def build_autonomy_contract(
    *,
    model_plan: dict[str, Any],
    routing_decision: dict[str, Any],
    specialist_tasks: list[dict[str, Any]],
    configuration_tasks: list[dict[str, Any]],
    review_gate: dict[str, Any],
    execution_model: dict[str, Any],
    policy_summary: dict[str, Any],
    collaboration_enabled: bool,
    controller_enabled: bool,
    scheduled: bool = False,
) -> dict[str, Any]:
    reasons: list[str] = []
    blockers: list[str] = []
    requires_human = False
    model_strategy = str(model_plan.get("strategy") or "")
    routing_status = str(routing_decision.get("status") or "")
    has_specialists = bool(specialist_tasks)
    has_multiple_specialists = len(specialist_tasks) > 1
    supervised_side_effect_count = sum(1 for task in specialist_tasks if task_requires_supervision(task))

    if routing_status in {"ambiguous", "low-confidence"}:
        requires_human = True
        blockers.append("routing-confirmation-required")
        reasons.append("Routing requires human confirmation.")
    if configuration_tasks:
        requires_human = True
        blockers.append("provider-configuration-required")
        reasons.append("Provider/source configuration is required.")
    if model_strategy == "human":
        requires_human = True
        blockers.append("human-model-strategy")
        reasons.append("Model strategy selected human input.")
    if supervised_side_effect_count:
        requires_human = True
        blockers.append("write-policy-confirmation-required")
        reasons.append("One or more tasks require explicit confirmation by write policy.")

    if scheduled:
        level = 4
        reasons.append("Execution is scheduled.")
    elif requires_human and supervised_side_effect_count:
        level = 3
    elif requires_human:
        level = 1
    elif controller_enabled and collaboration_enabled and has_multiple_specialists:
        level = 6
        reasons.append("Controller can execute a composed specialist workflow within declared limits.")
    elif collaboration_enabled and has_multiple_specialists:
        level = 5
        reasons.append("Plan coordinates multiple specialist agents.")
    elif model_strategy == "automation" and has_specialists:
        level = 2
        reasons.append("Plan maps to deterministic autonomous-safe capability execution.")
    elif has_specialists:
        level = 2 if int(policy_summary.get("autonomous_safe") or 0) > 0 else 1
        reasons.append("Plan selected known capability contracts.")
    else:
        level = 1
        reasons.append("Plan needs reasoning, user input, or a configured LLM before autonomous execution.")

    level_id, level_description = LEVELS[level]
    limits = execution_model.get("limits") if isinstance(execution_model.get("limits"), dict) else {}
    allowed_side_effects = (
        execution_model.get("allowed_side_effects")
        if isinstance(execution_model.get("allowed_side_effects"), dict)
        else {}
    )
    execution_allowed = not blockers and level in {2, 4, 5, 6}
    if model_strategy == "external-llm" and int(limits.get("max_llm_calls") or 0) > 0:
        execution_allowed = True
    if any(task_is_blocked_by_default(task) for task in specialist_tasks):
        execution_allowed = False

    status = "allowed" if execution_allowed else "needs-input" if requires_human else "planned"
    if any(task_is_blocked_by_default(task) for task in specialist_tasks):
        status = "blocked"

    return {
        "kind": "autonomy-contract",
        "schema_version": AUTONOMY_SCHEMA_VERSION,
        "level": level,
        "level_id": level_id,
        "level_description": level_description,
        "status": status,
        "execution_allowed": execution_allowed,
        "requires_human": requires_human,
        "requires_review": bool(review_gate.get("required")),
        "can_call_capabilities": bool(allowed_side_effects.get("can_call_capabilities")),
        "can_call_llm": allowed_side_effects.get("can_call_llm"),
        "can_schedule": level in {2, 4, 5, 6} and not requires_human,
        "audit_required": True,
        "model_strategy": model_strategy or None,
        "model_risk": model_plan.get("risk"),
        "routing_status": routing_status or None,
        "controller_enabled": bool(controller_enabled),
        "collaboration_enabled": bool(collaboration_enabled),
        "limits": limits,
        "policy_summary": policy_summary,
        "allowed_actions": allowed_actions_for_level(level, execution_allowed),
        "blocked_actions": blocked_actions_for(level, blockers, model_plan),
        "blockers": blockers,
        "reasons": reasons,
        "fallback": model_plan.get("fallback"),
    }


def build_task_autonomy_contract(
    task: dict[str, Any],
    *,
    origin: str,
    dry_run: bool = False,
    permission: dict[str, Any] | None = None,
) -> dict[str, Any]:
    action = task.get("action") if isinstance(task.get("action"), dict) else {}
    schedule = task.get("schedule") if isinstance(task.get("schedule"), dict) else {}
    notify = task.get("notify") if isinstance(task.get("notify"), dict) else {}
    permission = permission if isinstance(permission, dict) else {}
    scheduled = origin == "scheduler" or schedule.get("type") not in {None, "manual"}
    external_writes = action.get("external_writes") is True
    permission_ok = permission.get("ok") is not False
    requires_human = external_writes and not permission_ok
    level = 4 if scheduled else 0
    if requires_human:
        level = 3
    level_id, level_description = LEVELS[level]
    execution_allowed = dry_run or not requires_human
    status = "allowed" if execution_allowed else "needs-input"
    blockers = ["external-write-permission-required"] if requires_human else []
    return {
        "kind": "autonomy-contract",
        "schema_version": AUTONOMY_SCHEMA_VERSION,
        "level": level,
        "level_id": level_id,
        "level_description": level_description,
        "status": status,
        "execution_allowed": execution_allowed,
        "requires_human": requires_human,
        "requires_review": external_writes,
        "can_call_capabilities": action.get("type") == "capability",
        "can_call_llm": action.get("type") == "prompt",
        "can_schedule": scheduled,
        "audit_required": origin == "scheduler",
        "scheduled": scheduled,
        "notification_required": bool(task.get("notifications") or notify),
        "allowed_actions": allowed_actions_for_level(level, execution_allowed),
        "blocked_actions": blocked_actions_for(level, blockers, {}),
        "blockers": blockers,
        "reasons": task_autonomy_reasons(scheduled=scheduled, external_writes=external_writes, dry_run=dry_run),
    }


def task_requires_supervision(task: dict[str, Any]) -> bool:
    metadata = task.get("write_policy_metadata") if isinstance(task.get("write_policy_metadata"), dict) else {}
    return bool(metadata.get("requires_confirmation") or metadata.get("blocked_by_default"))


def task_is_blocked_by_default(task: dict[str, Any]) -> bool:
    metadata = task.get("write_policy_metadata") if isinstance(task.get("write_policy_metadata"), dict) else {}
    return bool(metadata.get("blocked_by_default"))


def allowed_actions_for_level(level: int, execution_allowed: bool) -> list[str]:
    if not execution_allowed:
        return ["dry-run", "ask-human"]
    actions = ["audit", "notify"]
    if level >= 2:
        actions.append("run-autonomous-safe-capability")
    if level >= 4:
        actions.append("run-scheduled-task")
    if level >= 5:
        actions.append("coordinate-specialists")
    if level >= 6:
        actions.append("run-controlled-workflow")
    return actions


def blocked_actions_for(level: int, blockers: list[str], model_plan: dict[str, Any]) -> list[str]:
    blocked = set(model_plan.get("forbidden_actions") or [])
    if blockers:
        blocked.update({"execute-without-human-input", "external-write"})
    if level < 4:
        blocked.add("unbounded-loop")
    blocked.add("destructive-action-without-confirmation")
    return sorted(blocked)


def task_autonomy_reasons(*, scheduled: bool, external_writes: bool, dry_run: bool) -> list[str]:
    reasons = []
    if scheduled:
        reasons.append("Task is managed by the local scheduler contract.")
    else:
        reasons.append("Task is a manual local task run.")
    if external_writes:
        reasons.append("Task declares external write effects.")
    if dry_run:
        reasons.append("Dry-run permits planning without external effects.")
    return reasons


def summarize_autonomy_contract(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {
        "schema_version": value.get("schema_version"),
        "level": value.get("level"),
        "level_id": value.get("level_id"),
        "status": value.get("status"),
        "execution_allowed": value.get("execution_allowed") is True,
        "requires_human": value.get("requires_human") is True,
        "requires_review": value.get("requires_review") is True,
        "model_strategy": value.get("model_strategy"),
        "model_risk": value.get("model_risk"),
        "blockers": list(value.get("blockers") or []),
    }
