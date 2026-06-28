"""Agent and capability registry helpers for orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_agent_registry(root: Path) -> dict[str, Any]:
    agents_dir = root / "agents"
    agents: dict[str, dict[str, Any]] = {}
    capabilities: dict[str, dict[str, Any]] = {}
    if not agents_dir.exists():
        return {"agents": agents, "capabilities": capabilities}
    for agent_path in sorted(path for path in agents_dir.iterdir() if path.is_dir()):
        manifest_path = agent_path / "agent.yaml"
        if not manifest_path.exists():
            continue
        agent = read_yaml(manifest_path)
        agent_id = str(agent.get("id") or agent_path.name)
        agent["id"] = agent_id
        agent["path"] = str(agent_path.relative_to(root))
        agent["capabilities_index"] = {}
        for capability_path in sorted((agent_path / "capabilities").glob("*/capability.yaml")):
            capability = read_yaml(capability_path)
            capability_id = str(capability.get("id") or capability_path.parent.name)
            short_id = capability_id.rsplit(".", 1)[-1]
            public_capability = {
                "id": capability_id,
                "short_id": short_id,
                "agent_id": agent_id,
                "name": capability.get("name") or short_id,
                "purpose": compact(str(capability.get("purpose") or "")),
                "write_policy": capability.get("write_policy"),
                "inputs": capability.get("inputs") or {},
                "outputs": capability.get("outputs") or {},
                "integration": capability.get("integration") or {},
                "requires": capability.get("requires") or {},
                "has_runner": bool(((capability.get("entrypoint") or {}).get("runner"))),
                "path": str(capability_path.parent.relative_to(root)),
            }
            agent["capabilities_index"][short_id] = public_capability
            capabilities[f"{agent_id}/{short_id}"] = public_capability
        agents[agent_id] = public_agent(agent)
    return {"agents": agents, "capabilities": capabilities}


def public_agent(agent: dict[str, Any]) -> dict[str, Any]:
    surface = agent.get("agent_surface") if isinstance(agent.get("agent_surface"), dict) else {}
    return {
        "id": agent.get("id"),
        "name": agent.get("name") or agent.get("id"),
        "kind": agent.get("kind"),
        "status": agent.get("status"),
        "purpose": compact(str(agent.get("purpose") or "")),
        "depends_on_agents": list(agent.get("depends_on_agents") or []),
        "orchestrated_agents": list(surface.get("orchestrated_agents") or []),
        "capabilities": list(agent.get("capabilities") or []),
        "capabilities_index": dict(agent.get("capabilities_index") or {}),
        "write_policy": agent.get("write_policy"),
        "path": agent.get("path"),
    }


def find_capability(registry: dict[str, Any], agent_id: str, capability_id: str) -> dict[str, Any] | None:
    return (registry.get("capabilities") or {}).get(f"{agent_id}/{capability_id}")


def read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def compact(value: str, *, limit: int = 240) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
