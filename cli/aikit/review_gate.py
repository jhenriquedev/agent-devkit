"""Mandatory review gate decisions before completing agentic work."""

from __future__ import annotations

import re
from typing import Any


REVIEW_REQUIRED_PATTERN = re.compile(
    r"(?i)\b(c[oó]digo|software|documento|spec|especifica|requisit|plano|automac|pr|pull request|deploy|infra|sql|banco|seguran)\b"
)


def build_review_gate(prompt: str, *, route: dict[str, Any] | None = None, model_plan: dict[str, Any] | None = None) -> dict[str, Any]:
    required = bool(REVIEW_REQUIRED_PATTERN.search(prompt))
    if route:
        required = True
    if model_plan and (model_plan.get("local_llm_selected") or model_plan.get("local_llm_recommended")):
        required = True
    return {
        "kind": "review-gate",
        "required": required,
        "status": "pending" if required else "not-required",
        "preferred_reviewers": ["claude-code", "codex-cli"],
        "reason": (
            "Deliverable or delegated local-LLM work requires coordinator review before completion."
            if required
            else "Prompt does not require a formal review gate."
        ),
        "route": route,
    }


def mark_reviewed(payload: dict[str, Any], *, reviewer: str | None = None, notes: str | None = None) -> dict[str, Any]:
    gate = dict(payload)
    if gate.get("required"):
        gate["status"] = "reviewed"
        gate["reviewer"] = reviewer or "coordinator"
        gate["notes"] = notes or "Reviewed by the active coordinator before final response."
    return gate
