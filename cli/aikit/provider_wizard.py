"""Backward-compatible provider wizard wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.aikit.configuration_orchestrator import provider_setup_wizard


def missing_source_wizard(prompt: str, route: dict[str, Any], *, root: Path | None = None) -> dict[str, Any]:
    provider = str(route.get("provider") or "")
    return provider_setup_wizard(
        root or Path(__file__).resolve().parents[2],
        provider,
        prompt=prompt,
        route=route,
        reason="No reusable source is configured for this routed prompt.",
    )
