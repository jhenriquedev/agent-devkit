"""Shared setup wizard payload helpers."""

from __future__ import annotations

from typing import Any

from cli.aikit.wizard_state import create_provider_wizard


def persist_setup_wizard_payload(
    payload: dict[str, Any],
    *,
    execution_plan: dict[str, Any] | None = None,
    route: dict[str, Any] | None = None,
) -> dict[str, Any]:
    wizard = payload.get("setup_wizard")
    if not isinstance(wizard, dict) or wizard.get("wizard_id"):
        return payload
    if wizard.get("status") == "denied-by-user":
        payload["next_question"] = wizard.get("next_question")
        return payload
    persisted = create_provider_wizard(
        wizard,
        execution_plan=execution_plan or payload.get("execution_plan"),
        route=route or payload.get("route"),
    )
    payload["setup_wizard"] = persisted
    payload["next_question"] = persisted.get("next_question")
    if execution_plan and execution_plan.get("configuration_tasks"):
        for task in execution_plan.get("configuration_tasks") or []:
            if isinstance(task, dict) and task.get("provider") == persisted.get("provider"):
                task["setup_wizard"] = persisted
                break
    payload.setdefault("wizard_id", persisted.get("wizard_id"))
    return payload
