"""Explain Agent DevKit routing decisions without executing capabilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.aikit.agent_registry import find_capability, load_agent_registry
from cli.aikit.memory import redact_secrets
from cli.aikit.orchestrator import decide_routing
from cli.aikit.router import route_prompt
from cli.aikit.runtime_paths import ROOT


ROUTE_EXPLAIN_SCHEMA_VERSION = "agent-devkit.route-explain/v1"


def explain_route(prompt: str, root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    prompt = (prompt or "").strip()
    registry = load_agent_registry(root)
    deterministic_route = route_prompt(prompt, root=root)
    decision = decide_routing(registry, prompt, deterministic_route)
    selected_agent = decision.get("selected_agent_id")
    selected_capability = decision.get("selected_capability_id")
    capability = (
        find_capability(registry, str(selected_agent), str(selected_capability))
        if selected_agent and selected_capability
        else None
    )
    blockers = blockers_for_capability(capability)
    route_status = str(decision.get("status") or "")
    has_executable_selection = bool(selected_agent and selected_capability)
    explain_decision = "selected" if route_status in {"selected", "deterministic"} and has_executable_selection else "needs-input"
    return {
        "kind": "route-explain",
        "schema_version": ROUTE_EXPLAIN_SCHEMA_VERSION,
        "status": "ok",
        "execution": "not-executed",
        "prompt": redact_secrets(prompt),
        "normalized_prompt": " ".join(prompt.lower().split()),
        "intent": intent_for(decision, deterministic_route),
        "decision": explain_decision,
        "routing_status": route_status,
        "selected": {
            "agent_id": selected_agent,
            "capability_id": selected_capability,
        },
        "score": decision.get("score"),
        "confidence": decision.get("confidence"),
        "confidence_label": decision.get("confidence_label"),
        "method": decision.get("method"),
        "signals": signal_summary(decision),
        "candidates": normalize_candidates(decision.get("candidates") or []),
        "providers_required": providers_for_capability(capability),
        "source_contract": (capability or {}).get("source_contract"),
        "write_policy": (capability or {}).get("write_policy"),
        "write_policy_metadata": (capability or {}).get("write_policy_metadata"),
        "missing_configuration": blockers,
        "will_use": {
            "automation": bool(capability and capability.get("has_runner")),
            "mini_brain": False,
            "external_llm": False,
            "human": explain_decision == "needs-input",
        },
        "reason": decision.get("reason"),
        "question": decision.get("question"),
        "options": decision.get("options") or [],
        "next_step": next_step(explain_decision, selected_agent, selected_capability, blockers),
    }


def intent_for(decision: dict[str, Any], deterministic_route: dict[str, Any] | None) -> str | None:
    if deterministic_route and deterministic_route.get("intent"):
        return str(deterministic_route["intent"])
    entities = decision.get("entities") if isinstance(decision.get("entities"), dict) else {}
    if entities.get("pr_id"):
        return "pull-request"
    if entities.get("card_id"):
        return "card"
    selected = decision.get("selected_capability_id")
    return str(selected) if selected else None


def normalize_candidates(candidates: list[Any]) -> list[dict[str, Any]]:
    normalized = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        normalized.append(
            {
                "agent_id": candidate.get("agent_id"),
                "capability_id": candidate.get("selected_capability_id") or candidate.get("capability_id"),
                "score": candidate.get("score"),
                "signals": {
                    key: candidate.get(key)
                    for key in sorted(candidate)
                    if key.startswith("matched_") or key.startswith("selected_capability_matched_")
                },
                "legacy_fallback": candidate.get("legacy_fallback") is True,
            }
        )
    return normalized


def signal_summary(decision: dict[str, Any]) -> list[str]:
    signals = []
    for candidate in normalize_candidates(decision.get("candidates") or [])[:1]:
        for key, values in (candidate.get("signals") or {}).items():
            if values:
                signals.append(f"{key}: {', '.join(str(value) for value in values[:3])}")
    return signals


def providers_for_capability(capability: dict[str, Any] | None) -> list[str]:
    if not capability:
        return []
    providers = []
    provider = capability.get("provider")
    if provider:
        providers.append(str(provider))
    requires = capability.get("requires") if isinstance(capability.get("requires"), dict) else {}
    for item in requires.get("providers") or []:
        if isinstance(item, dict) and item.get("id") and str(item["id"]) not in providers:
            providers.append(str(item["id"]))
    return providers


def blockers_for_capability(capability: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not capability:
        return []
    blockers = []
    for provider in providers_for_capability(capability):
        blockers.append({"type": "provider-readiness", "provider": provider, "status": "not-checked"})
    return blockers


def next_step(
    decision: str,
    selected_agent: Any,
    selected_capability: Any,
    blockers: list[dict[str, Any]],
) -> str:
    if decision != "selected":
        if selected_agent and not selected_capability:
            return f"Choose a capability for agent `{selected_agent}` before execution."
        return "Ask the user to choose an agent/capability or provide more context."
    if blockers:
        return "Check provider/source readiness before execution."
    if selected_agent and selected_capability:
        return f"Run `agent run {selected_agent} {selected_capability}` if execution is desired."
    return "Review routing decision before execution."
