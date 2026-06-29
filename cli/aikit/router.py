"""Deterministic prompt router for common AI DevKit tasks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cli.aikit.agent_registry import load_agent_registry


CARD_PATTERN = re.compile(r"\b(?:card|cartao|tarefa|work\s*item)\s*#?(\d{2,})\b", re.IGNORECASE)


def route_prompt(prompt: str, root: Path | None = None) -> dict[str, Any] | None:
    card_match = CARD_PATTERN.search(prompt)
    if card_match:
        card_id = card_match.group(1)
        target = card_route_target(root)
        if not target:
            return None
        return card_route(card_id, target=target)
    return None


def card_route(card_id: str, *, target: dict[str, str]) -> dict[str, Any]:
    return {
        "intent": "card",
        "agent_id": target["agent_id"],
        "capability_id": target["capability_id"],
        "provider": target["provider"],
        "args": ["--id", card_id, "--include-comments"],
        "entities": {
            "card_id": card_id,
        },
        "confidence": "deterministic",
    }


def card_route_target(root: Path | None) -> dict[str, str] | None:
    if root is None:
        root = Path.cwd()
    registry = load_agent_registry(root)
    for capability in (registry.get("capabilities") or {}).values():
        if not isinstance(capability, dict):
            continue
        routing = capability.get("routing") if isinstance(capability.get("routing"), dict) else {}
        intents = set(routing.get("intents") or [])
        if "work-item.card.read" not in intents:
            continue
        agent_id = str(capability.get("agent_id") or "")
        capability_id = str(capability.get("short_id") or "")
        provider = str(capability.get("provider") or "")
        if agent_id and capability_id and provider:
            return {"agent_id": agent_id, "capability_id": capability_id, "provider": provider}
    return None
