"""Mandatory review gate decisions before completing agentic work."""

from __future__ import annotations

import re
from typing import Any


REVIEW_REQUIRED_PATTERN = re.compile(
    r"(?i)\b(c[oó]digo|software|documento|spec|especifica|requisit|plano|automac|pr|pull request|deploy|infra|sql|banco|seguran)\b"
)


def build_review_gate(
    prompt: str,
    *,
    route: dict[str, Any] | None = None,
    model_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    required = bool(REVIEW_REQUIRED_PATTERN.search(prompt))
    reasons: list[str] = []
    if required:
        reasons.append("deliverable")
    if route:
        required = True
        reasons.append("deterministic-route")
    if model_plan and (model_plan.get("local_llm_selected") or model_plan.get("local_llm_recommended")):
        required = True
        reasons.append("local-llm")
    if model_plan and model_plan.get("strategy") == "human":
        required = True
        reasons.append("human-strategy")
    if model_plan and model_plan.get("strategy") == "mini-brain":
        required = True
        reasons.append("mini-brain")
    if model_plan and model_plan.get("risk") == "high":
        required = True
        reasons.append("high-risk")
    if model_plan and model_plan.get("strategy") == "external-llm" and REVIEW_REQUIRED_PATTERN.search(prompt):
        required = True
        reasons.append("external-llm-deliverable")
    return {
        "kind": "review-gate",
        "required": required,
        "status": "pending" if required else "not-required",
        "preferred_reviewers": ["claude-code", "codex-cli"],
        "reason": review_reason(reasons) if required else "Prompt does not require a formal review gate.",
        "triggers": sorted(set(reasons)),
        "route": route,
    }


def mark_reviewed(payload: dict[str, Any], *, reviewer: str | None = None, notes: str | None = None) -> dict[str, Any]:
    gate = dict(payload)
    if gate.get("required"):
        gate["status"] = "reviewed"
        gate["reviewer"] = reviewer or "coordinator"
        gate["notes"] = notes or "Reviewed by the active coordinator before final response."
    return gate


def review_reason(reasons: list[str]) -> str:
    unique = sorted(set(reasons))
    if "human-strategy" in unique:
        return "Human model strategy requires explicit input before completion."
    if "high-risk" in unique:
        return "High-risk model strategy requires coordinator review before completion."
    if "mini-brain" in unique or "local-llm" in unique:
        return "Mini-brain or delegated local-LLM work requires coordinator review before completion."
    if "external-llm-deliverable" in unique:
        return "External LLM deliverable requires coordinator review before completion."
    return "Deliverable or routed work requires coordinator review before completion."
