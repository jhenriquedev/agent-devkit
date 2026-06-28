"""Task-to-model routing decisions for Agent DevKit."""

from __future__ import annotations

import re
from typing import Any

from cli.aikit.llm import llm_preference, load_config
from cli.aikit.ollama import ollama_status


OPERATIONAL_PATTERN = re.compile(
    r"(?i)\b(resum|sumari|classifi|extra(?:i|ir)|normaliz|compar|logs?|rascunho|agrupe|agrupar)\b"
)
HIGH_LEVEL_PATTERN = re.compile(
    r"(?i)\b(arquitet|decid|aprovar|reprovar|especifica|requisit|implemente|codigo|c[oó]digo|documento|automac|deploy|seguran)\b"
)


def build_model_plan(prompt: str, *, route: dict[str, Any] | None = None) -> dict[str, Any]:
    preference = llm_preference(load_config())
    ollama = ollama_status()
    local_available = ollama.get("status") == "ok"
    operational = bool(OPERATIONAL_PATTERN.search(prompt))
    high_level = bool(HIGH_LEVEL_PATTERN.search(prompt))
    use_local = operational and local_available
    return {
        "kind": "model-plan",
        "status": "planned",
        "intent": route.get("intent") if route else "llm",
        "primary_coordinators": coordinator_order(preference),
        "local_llm_role": "operational-worker",
        "local_llm_available": local_available,
        "local_llm_provider": "ollama",
        "local_llm_recommended": operational,
        "local_llm_selected": use_local,
        "delegation": {
            "allowed": operational,
            "selected": use_local,
            "reason": local_reason(operational=operational, local_available=local_available, high_level=high_level),
            "forbidden_actions": [
                "final-review",
                "external-write",
                "permission-decision",
                "architecture-decision",
                "pr-approval",
            ],
        },
        "fallback_order": preference.get("order") or [],
        "route": route,
    }


def coordinator_order(preference: dict[str, Any]) -> list[str]:
    order = list(preference.get("order") or [])
    preferred = [item for item in order if item in {"claude-code", "codex-cli"}]
    for item in ("claude-code", "codex-cli"):
        if item not in preferred:
            preferred.append(item)
    return preferred


def local_reason(*, operational: bool, local_available: bool, high_level: bool) -> str:
    if operational and local_available and high_level:
        return "Use Ollama for operational preprocessing; coordinator review remains mandatory."
    if operational and local_available:
        return "Task is operational and local Ollama is available."
    if operational and not local_available:
        return "Task is operational, but Ollama is not available; coordinator/API fallback should execute."
    return "Task requires coordinator-level reasoning or review."
