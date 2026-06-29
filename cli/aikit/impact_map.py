"""Technical ownership and impact map for Agent DevKit changes."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


OWNERSHIP_AREAS: list[dict[str, Any]] = [
    {
        "id": "cli",
        "name": "CLI",
        "paths": [
            "cli/aikit/main.py",
            "cli/aikit/cli_parser.py",
            "cli/aikit/cli_dispatch.py",
            "cli/aikit/human_output.py",
            "agent",
            "aikit",
            "ai-devkit",
        ],
        "responsibilities": [
            "argument parsing",
            "public commands",
            "human and JSON output",
            "exit codes",
            "TTY-facing behavior",
        ],
        "should_not_contain": [
            "agent domain rules",
            "provider-specific knowledge",
            "capability-only contracts",
        ],
    },
    {
        "id": "core_execution",
        "name": "Core De Planejamento E Execucao",
        "paths": [
            "cli/aikit/orchestrator.py",
            "cli/aikit/agent_executor.py",
            "cli/aikit/capability_runtime.py",
            "cli/aikit/core/*",
        ],
        "responsibilities": [
            "execution planning",
            "task selection",
            "capability execution",
            "guardrail entry points",
            "review gate integration",
        ],
        "should_not_contain": [
            "host-specific adapters",
            "provider credentials",
            "large prompt knowledge",
        ],
    },
    {
        "id": "registry",
        "name": "Registry",
        "paths": [
            "cli/aikit/agent_registry.py",
            "agents/*/agent.yaml",
            "agents/*/capabilities/*/capability.yaml",
        ],
        "responsibilities": [
            "agent loading",
            "capability loading",
            "declarative metadata normalization",
            "manifest contract exposure",
        ],
        "should_not_contain": [
            "runner execution logic",
            "duplicated YAML readers",
            "provider transport code",
        ],
    },
    {
        "id": "policies_guardrails",
        "name": "Policies E Guardrails",
        "paths": [
            "cli/aikit/write_policy.py",
            "cli/aikit/guardrails.py",
            "cli/aikit/permissions.py",
            "cli/aikit/review_gate.py",
        ],
        "responsibilities": [
            "canonical write policy",
            "confirmation requirements",
            "permission checks",
            "blocked-by-default behavior",
        ],
        "should_not_contain": [
            "provider implementation details",
            "capability-specific business rules",
            "host login flow",
        ],
    },
    {
        "id": "providers_sources",
        "name": "Providers, Credentials E Sources",
        "paths": [
            "cli/aikit/providers.py",
            "cli/aikit/credentials.py",
            "cli/aikit/sources.py",
            "cli/aikit/fallback.py",
            "providers/*.yaml",
            "agents/*/infra/integrations/*",
        ],
        "responsibilities": [
            "provider registry",
            "credential references",
            "provider readiness",
            "fallback behavior",
            "source configuration",
        ],
        "should_not_contain": [
            "hardcoded secrets",
            "mandatory host coupling",
            "agent prompt policy",
        ],
    },
    {
        "id": "llm_mini_brain",
        "name": "LLMs E Mini Cerebro",
        "paths": [
            "cli/aikit/llm.py",
            "cli/aikit/model_router.py",
            "cli/aikit/local_llm_operator.py",
            "cli/aikit/ollama.py",
        ],
        "responsibilities": [
            "LLM backend registry",
            "backend preference and fallback",
            "local model operation",
            "decision limits for simple conversation",
        ],
        "should_not_contain": [
            "provider-specific domain repositories",
            "scheduler persistence",
            "host-specific tool schemas",
        ],
    },
    {
        "id": "sessions_memory_tasks_scheduler",
        "name": "Sessions, Memory, Tasks E Scheduler",
        "paths": [
            "cli/aikit/sessions.py",
            "cli/aikit/memory.py",
            "cli/aikit/tasks.py",
            "cli/aikit/scheduler.py",
            "cli/aikit/calendar.py",
            "cli/aikit/notifications.py",
        ],
        "responsibilities": [
            "conversation continuity",
            "local state",
            "scheduled tasks",
            "calendar integration",
            "notifications",
        ],
        "should_not_contain": [
            "core routing policy",
            "provider transport internals",
            "manifest validation rules",
        ],
    },
    {
        "id": "audit",
        "name": "Auditoria",
        "paths": [
            "cli/aikit/audit.py",
            "cli/aikit/cli_dispatch.py",
            "cli/aikit/main.py",
        ],
        "responsibilities": [
            "operational trail",
            "redaction",
            "export",
            "execution origin",
            "audit warnings",
        ],
        "should_not_contain": [
            "business-domain analysis",
            "provider credentials",
            "large artifacts",
        ],
    },
    {
        "id": "mcp",
        "name": "MCP",
        "paths": [
            "cli/aikit/mcp_server.py",
            "cli/aikit/mcp_tools.py",
            "cli/aikit/mcp_manifest.py",
        ],
        "responsibilities": [
            "stdio server",
            "tool schemas",
            "calls into Agent DevKit core",
            "host-agnostic MCP surface",
        ],
        "should_not_contain": [
            "Hermes-only behavior",
            "OpenClaw-only behavior",
            "OpenCode-only behavior",
        ],
    },
    {
        "id": "validation_gates",
        "name": "Validacao E Gates",
        "paths": [
            "scripts/validate-repo.py",
            "scripts/release-gate.py",
            "tests/*",
            ".github/workflows/*",
        ],
        "responsibilities": [
            "repository structure validation",
            "manifest contracts",
            "release gates",
            "regression tests",
        ],
        "should_not_contain": [
            "runtime-only side effects",
            "provider credentials",
            "generated local docs",
        ],
    },
    {
        "id": "agents_capabilities",
        "name": "Agentes E Capabilities",
        "paths": [
            "agents/<agent-id>/agent.yaml",
            "agents/<agent-id>/AGENTS.md",
            "agents/<agent-id>/README.md",
            "agents/<agent-id>/capabilities/*",
            "agents/<agent-id>/knowledge/*",
            "agents/<agent-id>/templates/*",
            "agents/<agent-id>/infra/*",
        ],
        "responsibilities": [
            "domain ownership",
            "capability workflows",
            "runner behavior",
            "repositories",
            "templates",
            "on-demand knowledge",
        ],
        "should_not_contain": [
            "global runtime policy unless delegated",
            "unrelated agent changes",
            "host-specific core coupling",
        ],
    },
]


SPEC_IMPACT_TEMPLATE: dict[str, str] = {
    "likely_files": "Arquivos, modulos, manifests ou contratos provavelmente impactados.",
    "files_not_to_touch": "Arquivos e dominios que devem permanecer fora do patch.",
    "affected_contracts": "Contratos publicos, manifests, schemas, comandos ou payloads afetados.",
    "related_gates": "Testes, validators, release gates ou smoke tests relacionados.",
    "compatibility_risks": "Riscos de compatibilidade com CLI, hosts, agentes, providers ou usuarios existentes.",
    "boundary_crossing_justification": "Justificativa quando a mudanca cruza ownership de core, agente, provider, host ou gate.",
}


OWNERSHIP_RULES: list[str] = [
    "Identificar se a mudanca pertence a core, agente, provider, host, docs ou gate antes de implementar.",
    "Tocar apenas arquivos do ownership correto sempre que possivel.",
    "Justificar qualquer cruzamento de boundary no plano, PR ou resposta de entrega.",
    "Evitar alteracoes em massa de manifests sem spec explicita.",
    "Evitar alterar runtime central para resolver caso especifico de um agente.",
]


def ownership_area_ids() -> list[str]:
    """Return canonical technical ownership area identifiers."""
    return [area["id"] for area in OWNERSHIP_AREAS]


def spec_impact_template() -> dict[str, str]:
    """Return the canonical impact template for specs and PRs."""
    return dict(SPEC_IMPACT_TEMPLATE)


def ownership_model() -> dict[str, Any]:
    """Return the canonical technical ownership and impact model."""
    return {
        "schema_version": "ai-devkit.impact/v1",
        "areas": deepcopy(OWNERSHIP_AREAS),
        "spec_template": spec_impact_template(),
        "rules": list(OWNERSHIP_RULES),
    }
