"""Explicit agentic planning and orchestration CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.aikit.core.requests import AgentPromptRequest
from cli.aikit.errors import DevKitError
from cli.aikit.natural_prompt_runtime import run_agent_prompt_request
from cli.aikit.orchestrator import build_execution_plan
from cli.aikit.runtime_paths import ROOT


def agentic_plan(root: Path, prompt_parts: list[str] | tuple[str, ...] | None) -> dict[str, Any]:
    prompt = normalize_prompt(prompt_parts, command="plan")
    plan = build_execution_plan(root, prompt, dry_run=True)
    return {
        "kind": "agentic-plan",
        "status": plan.get("status") or "planned",
        "ok": True,
        "dry_run": True,
        "prompt_received": True,
        "prompt_length": len(prompt),
        "summary": plan_summary(plan),
        "execution_plan": plan,
        "orchestration_trace": plan.get("trace", []),
        "response": "Plano agentico gerado sem executar LLM, automacoes ou escritas externas.",
    }


def agentic_execute(
    prompt_parts: list[str] | tuple[str, ...] | None,
    *,
    llm: str | None = None,
    dry_run: bool = False,
    session_id: str | None = None,
    new_session: bool = False,
    no_llm_fallback: bool = False,
    prog_name: str = "agent",
    project: str | None = None,
    mode: str = "execute",
) -> dict[str, Any]:
    prompt = normalize_prompt(prompt_parts, command=mode)
    if dry_run:
        payload = agentic_plan(ROOT, [prompt])
        payload["command_mode"] = mode
        return payload
    result = run_agent_prompt_request(
        AgentPromptRequest(
            prompt=prompt,
            llm=llm,
            dry_run=False,
            session_id=session_id,
            new_session=new_session,
            no_llm_fallback=no_llm_fallback,
            prog_name=prog_name,
            project=project,
        )
    )
    return attach_agentic_metadata(result, prompt=prompt, mode=mode)


def normalize_prompt(prompt_parts: list[str] | tuple[str, ...] | None, *, command: str) -> str:
    prompt = " ".join(str(part) for part in (prompt_parts or [])).strip()
    if not prompt:
        raise DevKitError(f"agent {command} requires a natural-language prompt")
    return prompt


def plan_summary(plan: dict[str, Any]) -> dict[str, Any]:
    specialist_tasks = [task for task in plan.get("specialist_tasks") or [] if isinstance(task, dict)]
    configuration_tasks = [task for task in plan.get("configuration_tasks") or [] if isinstance(task, dict)]
    review_task = plan.get("review_task") if isinstance(plan.get("review_task"), dict) else {}
    model_plan = plan.get("model_plan") if isinstance(plan.get("model_plan"), dict) else {}
    routing_decision = plan.get("routing_decision") if isinstance(plan.get("routing_decision"), dict) else {}
    autonomy = plan.get("autonomy_contract") if isinstance(plan.get("autonomy_contract"), dict) else {}
    needs_input = (
        plan.get("status") == "needs-input"
        or bool(configuration_tasks)
        or model_plan.get("strategy") == "human"
        or autonomy.get("requires_human") is True
        or autonomy.get("status") == "needs-input"
    )
    return {
        "routing_status": routing_decision.get("status"),
        "selected_agent_id": routing_decision.get("selected_agent_id"),
        "selected_capability_id": routing_decision.get("selected_capability_id"),
        "model_strategy": model_plan.get("strategy"),
        "local_llm_selected": model_plan.get("local_llm_selected"),
        "specialist_tasks": len(specialist_tasks),
        "configuration_tasks": len(configuration_tasks),
        "review_required": bool(review_task.get("required") or review_task.get("status") in {"pending", "required"}),
        "collaboration_enabled": bool(plan.get("collaboration_enabled")),
        "controller_enabled": bool(plan.get("controller_enabled")),
        "needs_input": needs_input,
    }


def attach_agentic_metadata(result: dict[str, Any], *, prompt: str, mode: str) -> dict[str, Any]:
    plan = result.get("execution_plan") if isinstance(result.get("execution_plan"), dict) else None
    if plan is None:
        plan = local_shortcut_execution_plan(prompt=prompt, result=result, mode=mode)
        result["execution_plan"] = plan
    result.setdefault("orchestration_trace", plan.get("trace", []))
    result["agentic_summary"] = plan_summary(plan)
    result["command_mode"] = mode
    result["agentic_command"] = mode
    return result


def local_shortcut_execution_plan(*, prompt: str, result: dict[str, Any], mode: str) -> dict[str, Any]:
    status = str(result.get("status") or "ok")
    local_mode = str(result.get("mode") or result.get("action") or "local-shortcut")
    ok = result.get("ok") is not False and status not in {"blocked", "failed", "needs-input", "needs-review"}
    return {
        "schema_version": "ai-devkit.agentic-plan/v1",
        "status": "completed" if ok else status,
        "prompt": prompt,
        "dry_run": False,
        "command_mode": mode,
        "routing_decision": {
            "status": "selected",
            "selected_agent_id": "agent-devkit",
            "selected_capability_id": local_mode,
            "method": "local-shortcut",
            "confidence": 1.0,
        },
        "model_plan": {
            "strategy": "deterministic-local",
            "local_llm_selected": False,
            "local_llm_recommended": False,
            "fallback": None,
        },
        "specialist_tasks": [],
        "configuration_tasks": [],
        "review_task": {
            "agent_id": "execution-reviewer",
            "capability_id": "review-final-output",
            "status": "not-required",
            "required": False,
        },
        "review_gate": {
            "required": False,
            "status": "not-required",
            "reason": "local deterministic shortcut",
        },
        "collaboration_enabled": False,
        "controller_enabled": False,
        "trace": [
            {
                "agent_id": "task-orchestrator",
                "action": "local-shortcut",
                "mode": local_mode,
                "status": status,
            }
        ],
    }
