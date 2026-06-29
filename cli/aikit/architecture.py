"""Public architecture contract for Agent DevKit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.aikit.acceptance import acceptance_model
from cli.aikit.agent_registry import load_agent_registry
from cli.aikit.impact_map import ownership_model
from cli.aikit.roadmap import implementation_phases, problem_phase_map, recommended_initial_order
from cli.aikit.runtime_paths import ROOT


def architecture_contract(root: Path = ROOT) -> dict[str, Any]:
    registry = load_agent_registry(root)
    agents = registry.get("agents") or {}
    capabilities = registry.get("capabilities") or {}
    runtime_agents = sorted(
        agent_id
        for agent_id, agent in agents.items()
        if isinstance(agent, dict) and str(agent.get("kind") or "") == "runtime-agent"
    )
    specialist_agents = sorted(agent_id for agent_id in agents if agent_id not in set(runtime_agents))
    executable_capabilities = sum(
        1
        for capability in capabilities.values()
        if isinstance(capability, dict) and capability.get("has_runner")
    )
    return {
        "kind": "architecture",
        "schema_version": "ai-devkit.architecture/v1",
        "principal_agent": {
            "id": "agent-devkit",
            "name": "Agent DevKit",
            "role": "runtime-agent",
            "description": "Agente principal que coordena modulos especialistas, capabilities, automacoes, providers, memoria, guardrails e backends LLM.",
        },
        "model": {
            "agent_devkit": "agente principal",
            "agents": "modulos especialistas internos versionados em agents/*",
            "capabilities": "unidades executaveis do sistema",
            "runners": "automacoes deterministicas para tarefas conhecidas",
            "providers": "integracoes externas acessadas por contratos controlados",
            "llms": "cerebros plugaveis para conversa, decisao e revisao quando necessario",
            "hosts": "interfaces ou consumidores externos, como CLI, MCP, Codex, Claude, OpenClaw e OpenCode",
        },
        "core_responsibilities": [
            "planner_router",
            "memory_sessions",
            "permissions_guardrails",
            "audit",
            "provider_registry",
            "llm_backend_selection",
            "capability_execution",
            "review_gate",
        ],
        "decision_targets": [
            "deterministic_capability",
            "local_mini_brain",
            "external_professional_llm",
            "human_input",
            "external_provider",
            "external_host_via_mcp",
        ],
        "interfaces": [
            "cli",
            "mcp",
            "host_adapter",
        ],
        "implementation_phases": implementation_phases(),
        "recommended_initial_order": recommended_initial_order(),
        "problem_phase_map": problem_phase_map(),
        "acceptance_model": acceptance_model(),
        "impact_model": ownership_model(),
        "counts": {
            "runtime_agents": len(runtime_agents),
            "specialist_agents": len(specialist_agents),
            "capabilities": len(capabilities),
            "executable_capabilities": executable_capabilities,
        },
        "runtime_agents": runtime_agents,
        "status": "partially-implemented",
    }
