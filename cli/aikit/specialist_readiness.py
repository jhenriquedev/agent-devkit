"""Specialist agent readiness summaries for onboarding and doctor."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from cli.aikit.agent_registry import load_agent_registry
from cli.aikit.sources import list_sources, source_status


SPECIALIST_READINESS_SCHEMA_VERSION = "agent-devkit.specialist-readiness/v1"


def specialist_readiness(root: Path) -> dict[str, Any]:
    registry = load_agent_registry(root)
    capabilities = registry.get("capabilities") if isinstance(registry.get("capabilities"), dict) else {}
    agents = registry.get("agents") if isinstance(registry.get("agents"), dict) else {}
    source_summary = configured_source_summary()
    configured_providers = set(source_summary["configured_providers"])
    provider_capabilities: Counter[str] = Counter()
    agent_providers: dict[str, Counter[str]] = defaultdict(Counter)
    agent_capabilities: Counter[str] = Counter()
    source_enabled_capabilities: Counter[str] = Counter()

    for capability in capabilities.values():
        if not isinstance(capability, dict):
            continue
        agent_id = str(capability.get("agent_id") or "")
        if not agent_id:
            continue
        provider = str(capability.get("provider") or "").strip()
        if provider:
            provider_capabilities[provider] += 1
            agent_providers[agent_id][provider] += 1
            agent_capabilities[agent_id] += 1
        source_contract = capability.get("source_contract") if isinstance(capability.get("source_contract"), dict) else {}
        if source_contract.get("enabled") or source_contract.get("supported"):
            source_enabled_capabilities[agent_id] += 1

    items = [
        agent_readiness_item(
            agent_id,
            agents.get(agent_id) if isinstance(agents.get(agent_id), dict) else {},
            providers,
            configured_providers=configured_providers,
            source_enabled_count=source_enabled_capabilities.get(agent_id, 0),
        )
        for agent_id, providers in sorted(agent_providers.items())
    ]
    missing_provider_counts: Counter[str] = Counter()
    for item in items:
        missing_provider_counts.update(item["missing_providers"])

    blocked = [item for item in items if item["status"] == "needs-setup"]
    partial = [item for item in items if item["status"] == "partial"]
    ready = [item for item in items if item["status"] == "ready"]
    status = "ready"
    if blocked:
        status = "needs-setup"
    elif partial:
        status = "partial"
    return {
        "kind": "specialist-readiness",
        "schema_version": SPECIALIST_READINESS_SCHEMA_VERSION,
        "status": status,
        "agents_total": len(agents),
        "capabilities_total": len(capabilities),
        "agents_with_provider_requirements": len(items),
        "ready_agents": len(ready),
        "partial_agents": len(partial),
        "needs_setup_agents": len(blocked),
        "providers_required": [
            {"id": provider, "capabilities": count, "configured": provider in configured_providers}
            for provider, count in provider_capabilities.most_common()
        ],
        "configured_providers": sorted(configured_providers),
        "missing_providers": [
            {"id": provider, "agents": count}
            for provider, count in missing_provider_counts.most_common()
        ],
        "items": items,
        "source_summary": source_summary,
        "next_steps": readiness_next_steps(missing_provider_counts),
    }


def agent_readiness_item(
    agent_id: str,
    agent: dict[str, Any],
    providers: Counter[str],
    *,
    configured_providers: set[str],
    source_enabled_count: int,
) -> dict[str, Any]:
    required = sorted(providers)
    configured = sorted(provider for provider in required if provider in configured_providers)
    missing = sorted(provider for provider in required if provider not in configured_providers)
    status = "ready"
    if missing and configured:
        status = "partial"
    elif missing:
        status = "needs-setup"
    return {
        "id": agent_id,
        "name": agent.get("name") or agent_id,
        "status": status,
        "required_providers": required,
        "configured_providers": configured,
        "missing_providers": missing,
        "provider_capabilities": dict(sorted(providers.items())),
        "source_enabled_capabilities": source_enabled_count,
        "setup_commands": [f"agent provider configure {provider}" for provider in missing[:3]],
    }


def configured_source_summary() -> dict[str, Any]:
    sources = list_sources()
    try:
        status = source_status()
        status_items = status.get("items") if isinstance(status.get("items"), list) else []
    except Exception:  # noqa: BLE001 - readiness must remain diagnostic, not fatal.
        status = {"status": "missing", "items": []}
        status_items = []
    configured_providers = sorted(
        {
            str(item.get("provider"))
            for item in status_items
            if isinstance(item, dict) and item.get("status") == "ok" and item.get("provider")
        }
    )
    providers_with_sources = sorted(
        {
            str(item.get("provider"))
            for item in sources.get("items") or []
            if isinstance(item, dict) and item.get("provider")
        }
    )
    return {
        "status": status.get("status"),
        "sources_count": len(sources.get("items") or []),
        "configured_providers": configured_providers,
        "providers_with_sources": providers_with_sources,
        "stored_secret": sources.get("stored_secret") is True or status.get("stored_secret") is True,
    }


def readiness_next_steps(missing_provider_counts: Counter[str]) -> list[str]:
    if not missing_provider_counts:
        return []
    return [f"agent provider configure {provider}" for provider, _ in missing_provider_counts.most_common(5)]
