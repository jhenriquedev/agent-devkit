"""Task-to-model routing decisions for Agent DevKit."""

from __future__ import annotations

import re
from typing import Any

from cli.aikit.llm import BACKENDS, doctor_backend, llm_preference, load_config
from cli.aikit.mini_brain import mini_brain_contract
from cli.aikit.ollama import ollama_status
from cli.aikit.write_policy import normalize_write_policy, write_policy_public_fields


OPERATIONAL_PATTERN = re.compile(
    r"(?i)\b(resum\w*|sumari\w*|classifi\w*|extra(?:i|ir|ia|cao|ção)\w*|normaliz\w*|compar\w*|logs?|rascunho|agrupe|agrupar)\b"
)
HIGH_LEVEL_PATTERN = re.compile(
    r"(?i)\b(arquitet|decid|aprovar|reprovar|especifica|requisit|implemente|codigo|c[oó]digo|documento|automac|deploy|seguran)\b"
)
HUMAN_PATTERN = re.compile(
    r"(?i)\b(confirme|autorize|aprovar|aprovação|permiss[aã]o|delete|excluir|destrutiv)\b"
)
SENSITIVE_SECRET_ACTION_PATTERN = re.compile(
    r"(?i)(\b(mostre|exiba|revele|configure|alter[ea]|salve|envie|publique|registre|grave)\b.*\b(credencial|senha|token|segredo)\b|\b(credencial|senha|token|segredo)\b.*\b(mostre|exiba|revele|configure|alter[ea]|salve|envie|publique|registre|grave)\b)"
)

FORBIDDEN_ACTIONS = [
    "final-review",
    "external-write",
    "permission-decision",
    "architecture-decision",
    "pr-approval",
]


def build_model_plan(
    prompt: str,
    *,
    route: dict[str, Any] | None = None,
    routing_decision: dict[str, Any] | None = None,
    specialist_tasks: list[dict[str, Any]] | None = None,
    configuration_tasks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    config = load_config()
    preference = llm_preference(config)
    ollama = ollama_status()
    ollama_backend = doctor_backend(BACKENDS["ollama"], config)
    mini_brain = mini_brain_contract(config=config, ollama_payload=ollama, ollama_backend=ollama_backend)
    local_available = mini_brain.get("available") is True
    operational = bool(OPERATIONAL_PATTERN.search(prompt))
    high_level = bool(HIGH_LEVEL_PATTERN.search(prompt))
    policy = choose_model_strategy(
        prompt,
        route=route,
        routing_decision=routing_decision,
        specialist_tasks=specialist_tasks or [],
        configuration_tasks=configuration_tasks or [],
        operational=operational,
        high_level=high_level,
        local_available=local_available,
    )
    use_local = policy["strategy"] == "mini-brain" and local_available
    return {
        "kind": "model-plan",
        "status": "planned",
        "strategy": policy["strategy"],
        "reason": policy["reason"],
        "risk": policy["risk"],
        "confidence": policy["confidence"],
        "fallback": policy["fallback"],
        "forbidden_actions": list(policy["forbidden_actions"]),
        "decision_matrix": policy["decision_matrix"],
        "max_llm_calls": policy["max_llm_calls"],
        "intent": route.get("intent") if route else "llm",
        "primary_coordinators": coordinator_order(preference),
        "local_llm_role": "operational-worker",
        "local_llm_available": local_available,
        "local_llm_provider": mini_brain.get("provider") or "ollama",
        "local_llm_backend_configured": ollama_backend.get("status") == "ok",
        "local_llm_runtime": {
            "binary_status": ollama.get("status"),
            "backend_status": ollama_backend.get("status"),
            "model": mini_brain.get("ollama_model") or ollama_backend.get("model"),
            "base_url": ollama_backend.get("base_url"),
        },
        "mini_brain": mini_brain,
        "local_llm_recommended": operational,
        "local_llm_selected": use_local,
        "delegation": {
            "allowed": policy["strategy"] == "mini-brain",
            "selected": use_local,
            "reason": local_reason(
                operational=operational,
                local_available=local_available,
                high_level=high_level,
                strategy=policy["strategy"],
            ),
            "forbidden_actions": list(policy["forbidden_actions"]),
        },
        "fallback_order": preference.get("order") or [],
        "route": route,
    }


def choose_model_strategy(
    prompt: str,
    *,
    route: dict[str, Any] | None,
    routing_decision: dict[str, Any] | None,
    specialist_tasks: list[dict[str, Any]],
    configuration_tasks: list[dict[str, Any]],
    operational: bool,
    high_level: bool,
    local_available: bool,
) -> dict[str, Any]:
    routing_status = (routing_decision or {}).get("status")
    if routing_status in {"ambiguous", "low-confidence"}:
        return policy(
            "human",
            "Routing is ambiguous or low confidence, so a human must choose the agent/capability.",
            risk="medium",
            confidence="low",
            fallback="ask-user-to-confirm-route",
            max_llm_calls=0,
            matrix="Ambigua + risco/side effect -> humano",
        )
    if configuration_tasks:
        return policy(
            "human",
            "A provider/source configuration task is required before execution.",
            risk="medium",
            confidence="high",
            fallback="provider-setup-wizard",
            max_llm_calls=0,
            matrix="Credencial/config faltante -> humano",
        )
    if prompt_requires_human(prompt) or any(task_requires_confirmation(task) for task in specialist_tasks):
        return policy(
            "human",
            "The prompt or selected task requires human confirmation by policy.",
            risk="high",
            confidence="high",
            fallback="ask-human-confirmation",
            max_llm_calls=0,
            matrix="Ambigua + risco/side effect -> humano",
        )
    if route or has_executable_known_task(specialist_tasks):
        return policy(
            "automation",
            "The task maps to a known deterministic capability with controlled policy.",
            risk="low",
            confidence="high",
            fallback="manual-steps-if-provider-missing",
            max_llm_calls=0,
            matrix="Conhecida + estruturada + baixo risco -> automacao",
        )
    if operational and not high_level:
        return policy(
            "mini-brain" if local_available else "external-llm",
            "The prompt is operational and low-risk; local mini-brain is preferred when available.",
            risk="low",
            confidence="medium" if local_available else "low",
            fallback="external-llm" if local_available else "configure-local-mini-brain-or-use-external-llm",
            max_llm_calls=1,
            matrix="Simples + conversa/setup -> mini cerebro local",
        )
    return policy(
        "external-llm",
        "The task requires coordinator-level reasoning, synthesis, or open-ended judgment.",
        risk="medium" if not high_level else "high",
        confidence="medium",
        fallback="ask-human-if-review-or-backend-unavailable",
        max_llm_calls=1,
        matrix="Aberta + complexa + alto julgamento -> LLM externa",
    )


def policy(
    strategy: str,
    reason: str,
    *,
    risk: str,
    confidence: str,
    fallback: str,
    max_llm_calls: int,
    matrix: str,
) -> dict[str, Any]:
    return {
        "strategy": strategy,
        "reason": reason,
        "risk": risk,
        "confidence": confidence,
        "fallback": fallback,
        "forbidden_actions": FORBIDDEN_ACTIONS,
        "max_llm_calls": max_llm_calls,
        "decision_matrix": {
            "selected_rule": matrix,
            "priority": ["deterministic-rule", "local-automation", "mini-brain", "external-llm", "human"],
        },
    }


def has_executable_known_task(tasks: list[dict[str, Any]]) -> bool:
    return any(task.get("executable") and is_autonomous_safe_task(task) for task in tasks)


def is_autonomous_safe_task(task: dict[str, Any]) -> bool:
    metadata = task.get("write_policy_metadata") if isinstance(task.get("write_policy_metadata"), dict) else {}
    if metadata:
        return bool(metadata.get("autonomous_safe"))
    return bool(write_policy_public_fields(task.get("write_policy"))["write_policy_metadata"].get("autonomous_safe"))


def task_requires_confirmation(task: dict[str, Any]) -> bool:
    metadata = task.get("write_policy_metadata") if isinstance(task.get("write_policy_metadata"), dict) else {}
    if not metadata:
        metadata = write_policy_public_fields(normalize_write_policy(task.get("write_policy")))["write_policy_metadata"]
    return bool(metadata.get("requires_confirmation") or metadata.get("blocked_by_default"))


def prompt_requires_human(prompt: str) -> bool:
    return bool(HUMAN_PATTERN.search(prompt) or SENSITIVE_SECRET_ACTION_PATTERN.search(prompt))


def coordinator_order(preference: dict[str, Any]) -> list[str]:
    order = list(preference.get("order") or [])
    preferred = [item for item in order if item in {"claude-code", "codex-cli"}]
    for item in ("claude-code", "codex-cli"):
        if item not in preferred:
            preferred.append(item)
    return preferred


def local_reason(*, operational: bool, local_available: bool, high_level: bool, strategy: str) -> str:
    if strategy != "mini-brain":
        return "Local LLM delegation is not selected by the model strategy."
    if operational and local_available and high_level:
        return "Use the local mini-brain for operational preprocessing; coordinator review remains mandatory."
    if operational and local_available:
        return "Task is operational and the local mini-brain is enabled and available."
    if operational and not local_available:
        return "Task is operational, but the local mini-brain is not enabled or available; coordinator/API fallback should execute."
    return "Task requires coordinator-level reasoning or review."
