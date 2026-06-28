"""Deterministic prompt router for common AI DevKit tasks."""

from __future__ import annotations

import re
from typing import Any


CARD_PATTERN = re.compile(r"\b(?:card|cartao|tarefa|work\s*item)\s*#?(\d{2,})\b", re.IGNORECASE)


def route_prompt(prompt: str) -> dict[str, Any] | None:
    card_match = CARD_PATTERN.search(prompt)
    if card_match:
        card_id = card_match.group(1)
        return {
            "intent": "card",
            "agent_id": "azure-devops-orchestrator",
            "capability_id": "read-card",
            "provider": "azure-devops",
            "args": ["--id", card_id, "--include-comments"],
            "entities": {
                "card_id": card_id,
            },
            "confidence": "deterministic",
        }
    return None
