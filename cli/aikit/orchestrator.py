"""Multi-agent planning for natural-language Agent DevKit prompts."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from cli.aikit.agent_registry import find_capability, load_agent_registry
from cli.aikit.configuration_orchestrator import provider_setup_wizard
from cli.aikit.memory import redact_secrets
from cli.aikit.model_router import build_model_plan
from cli.aikit.review_gate import build_review_gate
from cli.aikit.router import route_prompt
from cli.aikit.sources import SourceRegistryError, public_source, resolve_source


RUNTIME_COORDINATOR = {
    "id": "task-orchestrator",
    "kind": "runtime-agent",
    "name": "Task Orchestrator",
    "role": "coordinator",
}
REVIEWER_AGENT_ID = "execution-reviewer"
PROVIDER_CONFIGURATOR_AGENT_ID = "provider-configurator"
LOCAL_LLM_OPERATOR_AGENT_ID = "local-llm-operator"
STOP_WORDS = {
    "a",
    "as",
    "com",
    "da",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "essa",
    "esse",
    "no",
    "na",
    "o",
    "os",
    "para",
    "por",
    "uma",
    "um",
}
TOKEN_ALIASES = {
    "analise": {"analysis", "analyze", "analisar"},
    "analisar": {"analysis", "analyze", "analise"},
    "cloudwatch": {"aws", "logs", "log"},
    "demanda": {"demand", "requirement", "requirements", "requisitos"},
    "erro": {"error", "errors", "falha"},
    "falha": {"error", "errors", "erro"},
    "gere": {"generate", "create", "criar"},
    "gerar": {"generate", "create", "criar"},
    "logs": {"log", "cloudwatch", "elasticsearch"},
    "servico": {"service", "serviço"},
    "especificacao": {"specification", "spec", "requirements", "requisitos"},
    "requisito": {"requirement", "requirements", "specification"},
    "requisitos": {"requirement", "requirements", "specification"},
    "tecnica": {"technical", "architecture", "component"},
    "tecnico": {"technical", "architecture", "component"},
}
AGENT_ANCHORS = {
    "aws-architecture-analyst": {"aws", "arquitetura", "architecture", "workload", "resiliencia", "observability", "vpc"},
    "aws-cloudwatch-log-analyzer": {"aws", "cloudwatch", "log", "logs"},
    "aws-operations-operator": {"aws", "ecs", "lambda", "sqs", "cloudfront", "eventbridge"},
    "aws-security-governance-auditor": {"aws", "iam", "s3", "cloudtrail", "security", "seguranca"},
    "azure-devops-orchestrator": {"azure", "devops", "card", "workitem", "work", "item", "board"},
    "bpo-analyser": {"bpo", "cpf", "proposta", "proposal"},
    "data-scientist-analyst": {"dataset", "dados", "data", "cohort", "modelo", "estatistica"},
    "database-change-operator": {"postgres", "migration", "migracao", "database", "banco"},
    "drawio-diagram-builder": {"drawio", "diagrama", "diagram"},
    "elasticsearch-log-analyzer": {"elasticsearch", "elastic", "indice", "index", "logs", "log"},
    "excel-workbook-builder": {"excel", "planilha", "spreadsheet", "workbook"},
    "figma-ui-ux-product-designer": {"figma", "ui", "ux", "design", "tela", "wireframe"},
    "github-pr-reviewer": {"github", "gh", "pr", "prs", "pull", "request"},
    "knowledge-generator": {"knowledge", "conhecimento", "documentacao", "runbook"},
    "postgres-data-analyzer": {"postgres", "postgresql", "sql", "database", "banco"},
    "presentation-deck-builder": {"apresentacao", "presentation", "slides", "powerpoint", "deck"},
    "software-specification-analyst": {"especificacao", "specification", "requisitos", "requirements", "historia", "stories", "demanda"},
    "sqlserver-change-operator": {"sqlserver", "sql", "migration", "migracao", "banco"},
    "sqlserver-data-analyzer": {"sqlserver", "sql", "database", "banco", "tabela"},
    "technical-integration-analyst": {"integracao", "integration", "api", "rest", "soap", "sftp", "mcp"},
    "topdesk-orchestrator": {"topdesk", "chamado"},
}


def build_execution_plan(root: Path, prompt: str, *, dry_run: bool = False) -> dict[str, Any]:
    registry = load_agent_registry(root)
    safe_prompt = redact_secrets(prompt)
    route = route_prompt(prompt)
    domain_agent = select_domain_agent(registry, prompt, route)
    specialist_tasks = specialist_tasks_for_prompt(registry, prompt, route, domain_agent)
    configuration_tasks = configuration_tasks_for(registry, root, prompt, route, specialist_tasks, dry_run=dry_run)
    model_plan = build_model_plan(prompt, route=route)
    model_plan = attach_local_llm_agent_contract(registry, model_plan)
    review_gate = build_review_gate(prompt, route=route, model_plan=model_plan)
    status = "needs-input" if configuration_tasks and not dry_run else "planned"
    return {
        "kind": "agentic-execution-plan",
        "schema_version": "ai-devkit.agentic-plan/v1",
        "status": status,
        "dry_run": dry_run,
        "prompt": safe_prompt,
        "coordinator_agent": runtime_agent(registry, "task-orchestrator", fallback=RUNTIME_COORDINATOR),
        "domain_agent": domain_agent,
        "route": route,
        "model_plan": model_plan,
        "review_gate": review_gate,
        "specialist_tasks": specialist_tasks,
        "configuration_tasks": configuration_tasks,
        "review_task": review_task(registry, review_gate),
        "executed_tasks": [],
        "blocked_tasks": [],
        "trace": trace_for_plan(specialist_tasks, configuration_tasks, status=status),
    }


def select_domain_agent(registry: dict[str, Any], prompt: str, route: dict[str, Any] | None) -> dict[str, Any]:
    normalized = normalize(prompt)
    agents = registry.get("agents") or {}
    if re.search(r"\bn1\b|primeiro nivel|1o nivel|1º nivel", normalized) and "n1-support-agent" in agents:
        return slim_agent(agents["n1-support-agent"])
    if re.search(r"\bn2\b|segundo nivel|2o nivel|2º nivel", normalized) and "n2-support-agent" in agents:
        return slim_agent(agents["n2-support-agent"])
    if route and route.get("agent_id") in agents:
        return slim_agent(agents[str(route["agent_id"])])
    matched_agent = best_agent_match(registry, prompt)
    if matched_agent:
        return slim_agent(matched_agent)
    if "task-orchestrator" in agents:
        return slim_agent(agents["task-orchestrator"])
    return dict(RUNTIME_COORDINATOR)


def specialist_tasks_for_prompt(
    registry: dict[str, Any],
    prompt: str,
    route: dict[str, Any] | None,
    domain_agent: dict[str, Any],
) -> list[dict[str, Any]]:
    if domain_agent.get("id") in {"n1-support-agent", "n2-support-agent"}:
        return orchestrated_tasks(registry, str(domain_agent["id"]), prompt, route)
    if route:
        task = task_from_route(registry, route)
        return [task] if task else []
    if domain_agent.get("id") and domain_agent.get("id") != "task-orchestrator":
        task = best_capability_task(registry, str(domain_agent["id"]), prompt)
        return [task] if task else []
    return []


def orchestrated_tasks(registry: dict[str, Any], agent_id: str, prompt: str, route: dict[str, Any] | None) -> list[dict[str, Any]]:
    agent = (registry.get("agents") or {}).get(agent_id) or {}
    tasks: list[dict[str, Any]] = []
    for pair in agent.get("orchestrated_agents") or []:
        if "/" not in str(pair):
            continue
        specialist_agent, capability_id = str(pair).split("/", 1)
        capability = find_capability(registry, specialist_agent, capability_id)
        if not capability:
            continue
        task = base_task(capability, prompt=prompt)
        if route and specialist_agent == route.get("agent_id") and capability_id == route.get("capability_id"):
            task["args"] = list(route.get("args") or [])
            task["entities"] = dict(route.get("entities") or {})
            task["provider"] = route.get("provider") or task.get("provider")
            task["primary"] = True
        tasks.append(task)
    if route and not any(task.get("primary") for task in tasks):
        routed = task_from_route(registry, route)
        if routed:
            routed["primary"] = True
            tasks.insert(0, routed)
    return tasks


def task_from_route(registry: dict[str, Any], route: dict[str, Any]) -> dict[str, Any] | None:
    capability = find_capability(registry, str(route.get("agent_id") or ""), str(route.get("capability_id") or ""))
    if not capability:
        return None
    task = base_task(capability, prompt="")
    task["args"] = list(route.get("args") or [])
    task["entities"] = dict(route.get("entities") or {})
    task["provider"] = route.get("provider") or task.get("provider")
    task["primary"] = True
    return task


def best_agent_match(registry: dict[str, Any], prompt: str) -> dict[str, Any] | None:
    prompt_tokens = expanded_tokens(prompt)
    normalized_prompt = normalize(prompt)
    best: tuple[int, dict[str, Any] | None] = (0, None)
    for agent in (registry.get("agents") or {}).values():
        if not has_agent_anchor(str(agent.get("id") or ""), prompt_tokens, normalized_prompt):
            continue
        agent_tokens = expanded_tokens(
            " ".join(
                [
                    str(agent.get("id") or ""),
                    str(agent.get("name") or ""),
                    str(agent.get("purpose") or ""),
                    " ".join(
                        " ".join(
                            [
                                str(capability.get("short_id") or ""),
                                str(capability.get("name") or ""),
                                str(capability.get("purpose") or ""),
                            ]
                        )
                        for capability in (agent.get("capabilities_index") or {}).values()
                        if isinstance(capability, dict)
                    ),
                ]
            )
        )
        score = weighted_overlap(prompt_tokens, agent_tokens)
        if score > best[0]:
            best = (score, agent)
    return best[1] if best[0] >= 3 else None


def has_agent_anchor(agent_id: str, prompt_tokens: set[str], normalized_prompt: str) -> bool:
    anchors = AGENT_ANCHORS.get(agent_id)
    if not anchors:
        return False
    if anchors & prompt_tokens:
        return True
    return any(anchor in normalized_prompt for anchor in anchors if len(anchor) >= 5)


def best_capability_task(registry: dict[str, Any], agent_id: str, prompt: str) -> dict[str, Any] | None:
    agent = (registry.get("agents") or {}).get(agent_id) or {}
    capabilities = [item for item in (agent.get("capabilities_index") or {}).values() if isinstance(item, dict)]
    if not capabilities:
        return None
    hinted = hinted_capability(capabilities, prompt)
    if hinted:
        task = base_task(hinted, prompt=prompt)
        task["primary"] = True
        task["selection"] = {"method": "registry-hint", "score": None}
        return task
    prompt_tokens = expanded_tokens(prompt)
    best: tuple[int, dict[str, Any] | None] = (0, None)
    for capability in capabilities:
        capability_tokens = expanded_tokens(
            " ".join(
                [
                    str(capability.get("short_id") or ""),
                    str(capability.get("name") or ""),
                    str(capability.get("purpose") or ""),
                ]
            )
        )
        score = weighted_overlap(prompt_tokens, capability_tokens)
        if score > best[0]:
            best = (score, capability)
    if not best[1] or best[0] < 2:
        return None
    task = base_task(best[1], prompt=prompt)
    task["primary"] = True
    task["selection"] = {"method": "registry-score", "score": best[0]}
    return task


def hinted_capability(capabilities: list[dict[str, Any]], prompt: str) -> dict[str, Any] | None:
    normalized = normalize(prompt)
    hints = []
    if "especificacao" in normalized and ("tecnica" in normalized or "tecnico" in normalized or "technical" in normalized):
        hints.append("create-technical-spec")
    if "especificacao" in normalized and ("funcional" in normalized or "functional" in normalized):
        hints.append("create-functional-spec")
    if "historia" in normalized or "user stor" in normalized:
        hints.append("write-user-stories")
    if "cloudwatch" in normalized and ("erro" in normalized or "error" in normalized):
        hints.append("analyze-service-error")
    if ("elasticsearch" in normalized or "elastic" in normalized) and ("erro" in normalized or "error" in normalized):
        hints.append("analyze-service-errors")
    for hint in hints:
        for capability in capabilities:
            if capability.get("short_id") == hint:
                return capability
    return None


def base_task(capability: dict[str, Any], *, prompt: str) -> dict[str, Any]:
    return {
        "id": f"{capability['agent_id']}.{capability['short_id']}",
        "agent_id": capability["agent_id"],
        "capability_id": capability["short_id"],
        "capability": capability["id"],
        "purpose": capability.get("purpose"),
        "write_policy": capability.get("write_policy") or "read_only",
        "provider": infer_provider(capability),
        "args": [],
        "entities": {},
        "status": "planned",
        "executable": bool(capability.get("has_runner")),
        "prompt": redact_secrets(prompt),
        "primary": False,
    }


def configuration_tasks_for(
    registry: dict[str, Any],
    root: Path,
    prompt: str,
    route: dict[str, Any] | None,
    specialist_tasks: list[dict[str, Any]],
    *,
    dry_run: bool,
) -> list[dict[str, Any]]:
    providers = []
    provider_agents: dict[str, str] = {}
    if route and route.get("provider"):
        providers.append(str(route["provider"]))
        if route.get("agent_id"):
            provider_agents[str(route["provider"])] = str(route["agent_id"])
    for task in specialist_tasks:
        provider = task.get("provider")
        if provider:
            provider_id = str(provider)
            providers.append(provider_id)
            provider_agents.setdefault(provider_id, str(task.get("agent_id") or ""))
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for provider in providers:
        if provider in seen:
            continue
        seen.add(provider)
        source = None
        agent_id = (route or {}).get("agent_id") or provider_agents.get(provider)
        try:
            source = resolve_source(provider=provider, intent=(route or {}).get("intent"), agent_id=agent_id)
        except SourceRegistryError:
            source = None
        if source:
            continue
        capability = find_capability(registry, PROVIDER_CONFIGURATOR_AGENT_ID, "configure-provider-source") or {}
        wizard = provider_setup_wizard(root, provider, prompt=prompt, route=route, reason="Provider/source required by multi-agent plan.")
        result.append(
            {
                "id": f"provider-configurator.{provider}",
                "agent_id": PROVIDER_CONFIGURATOR_AGENT_ID,
                "capability_id": "configure-provider-source",
                "capability": capability.get("id") or "provider-configurator.configure-provider-source",
                "purpose": capability.get("purpose"),
                "write_policy": capability.get("write_policy") or "local-config-write",
                "path": capability.get("path"),
                "provider": provider,
                "status": "waiting-for-user",
                "setup_wizard": wizard,
            }
        )
    return result


def attach_source_to_primary_task(plan: dict[str, Any]) -> dict[str, Any]:
    route = plan.get("route") if isinstance(plan.get("route"), dict) else None
    if not route:
        return plan
    try:
        source = resolve_source(provider=route.get("provider"), intent=route.get("intent"), agent_id=route.get("agent_id"))
    except SourceRegistryError:
        source = None
    if not source:
        return plan
    for task in plan.get("specialist_tasks") or []:
        if task.get("primary"):
            task["source"] = public_source(source)
            task["args"] = [*list(task.get("args") or []), "--source", str(source["id"])]
            task["status"] = "ready"
    plan["configuration_tasks"] = []
    if plan.get("status") == "needs-input":
        plan["status"] = "planned"
    return plan


def mark_plan_after_execution(plan: dict[str, Any], executed: list[dict[str, Any]], blocked: list[dict[str, Any]]) -> dict[str, Any]:
    plan = dict(plan)
    plan["executed_tasks"] = executed
    plan["blocked_tasks"] = blocked
    if blocked and not executed:
        plan["status"] = "blocked"
    elif blocked and executed:
        plan["status"] = "partial"
    elif executed:
        plan["status"] = "ok"
    plan["trace"] = trace_for_plan(plan.get("specialist_tasks") or [], plan.get("configuration_tasks") or [], executed=executed, blocked=blocked, status=plan["status"])
    return plan


def review_task(registry: dict[str, Any], review_gate: dict[str, Any]) -> dict[str, Any]:
    capability = find_capability(registry, REVIEWER_AGENT_ID, "review-final-output") or {}
    task = {
        "id": "execution-reviewer.review-final-output",
        "agent_id": REVIEWER_AGENT_ID,
        "capability_id": "review-final-output",
        "capability": capability.get("id") or "execution-reviewer.review-final-output",
        "purpose": capability.get("purpose"),
        "write_policy": capability.get("write_policy") or "read-only",
        "path": capability.get("path"),
        "status": "pending" if review_gate.get("required") else "not-required",
        "required": bool(review_gate.get("required")),
        "preferred_reviewers": list(review_gate.get("preferred_reviewers") or []),
    }
    return task


def mark_review_task(plan: dict[str, Any], *, reviewer: str) -> dict[str, Any]:
    task = dict(plan.get("review_task") or {"agent_id": REVIEWER_AGENT_ID, "capability_id": "review-final-output"})
    if task.get("required"):
        task["status"] = "reviewed"
        task["reviewer"] = reviewer
    plan["review_task"] = task
    return plan


def trace_for_plan(
    specialist_tasks: list[dict[str, Any]],
    configuration_tasks: list[dict[str, Any]],
    *,
    executed: list[dict[str, Any]] | None = None,
    blocked: list[dict[str, Any]] | None = None,
    status: str,
) -> list[dict[str, Any]]:
    trace = [{"agent_id": RUNTIME_COORDINATOR["id"], "action": "plan", "status": status}]
    trace.extend({"agent_id": task["agent_id"], "action": "configure", "status": task.get("status")} for task in configuration_tasks)
    trace.extend({"agent_id": task["agent_id"], "action": "execute", "status": task.get("status")} for task in specialist_tasks)
    trace.extend({"agent_id": item["agent_id"], "action": "executed", "status": item.get("status")} for item in executed or [])
    trace.extend({"agent_id": item["agent_id"], "action": "blocked", "status": item.get("status")} for item in blocked or [])
    return trace


def infer_provider(capability: dict[str, Any]) -> str | None:
    requires = capability.get("requires") if isinstance(capability.get("requires"), dict) else {}
    providers = requires.get("providers") if isinstance(requires.get("providers"), list) else []
    if providers and isinstance(providers[0], dict):
        return str(providers[0].get("id") or "") or None
    integration = capability.get("integration") if isinstance(capability.get("integration"), dict) else {}
    repository = str(integration.get("repository") or "")
    agent_id = str(capability.get("agent_id") or "")
    if "azure" in repository or agent_id == "azure-devops-orchestrator":
        return "azure-devops"
    if "topdesk" in repository or agent_id == "topdesk-orchestrator":
        return "topdesk"
    if "cloudwatch" in repository:
        return "aws-cloudwatch"
    if "elasticsearch" in repository:
        return "elasticsearch"
    if "sqlserver" in repository:
        return "sqlserver"
    if "postgres" in repository:
        return "postgres"
    if "/aws/" in repository or "aws-" in repository:
        return "aws"
    return None


def attach_local_llm_agent_contract(registry: dict[str, Any], model_plan: dict[str, Any]) -> dict[str, Any]:
    plan = dict(model_plan)
    agent = (registry.get("agents") or {}).get(LOCAL_LLM_OPERATOR_AGENT_ID)
    select_capability = find_capability(registry, LOCAL_LLM_OPERATOR_AGENT_ID, "select-local-worker") or {}
    delegate_capability = find_capability(registry, LOCAL_LLM_OPERATOR_AGENT_ID, "delegate-operational-task") or {}
    plan["operator_agent"] = slim_agent(agent) if isinstance(agent, dict) else {
        "id": LOCAL_LLM_OPERATOR_AGENT_ID,
        "name": "Local LLM Operator",
        "kind": "runtime-agent",
    }
    plan["selection_capability"] = {
        "agent_id": LOCAL_LLM_OPERATOR_AGENT_ID,
        "capability_id": "select-local-worker",
        "capability": select_capability.get("id") or "local-llm-operator.select-local-worker",
    }
    plan["delegation_capability"] = {
        "agent_id": LOCAL_LLM_OPERATOR_AGENT_ID,
        "capability_id": "delegate-operational-task",
        "capability": delegate_capability.get("id") or "local-llm-operator.delegate-operational-task",
    }
    return plan


def runtime_agent(registry: dict[str, Any], agent_id: str, *, fallback: dict[str, Any]) -> dict[str, Any]:
    agent = (registry.get("agents") or {}).get(agent_id)
    if isinstance(agent, dict):
        public = slim_agent(agent)
        public["role"] = fallback.get("role")
        return public
    return dict(fallback)


def slim_agent(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": agent.get("id"),
        "name": agent.get("name"),
        "kind": agent.get("kind") or "specialist-agent",
        "purpose": agent.get("purpose"),
        "path": agent.get("path"),
    }


def normalize(prompt: str) -> str:
    return " ".join(strip_accents(prompt).lower().split())


def strip_accents(value: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char))


def expanded_tokens(value: str) -> set[str]:
    tokens = {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9._-]*", normalize(value))
        if len(token) >= 3 and token not in STOP_WORDS
    }
    expanded = set(tokens)
    for token in tokens:
        expanded.update(TOKEN_ALIASES.get(token, set()))
        if token.endswith("s") and len(token) > 4:
            expanded.add(token[:-1])
    return expanded


def weighted_overlap(prompt_tokens: set[str], candidate_tokens: set[str]) -> int:
    score = 0
    for token in prompt_tokens:
        if token in candidate_tokens:
            score += 2
            continue
        if any(token in candidate or candidate in token for candidate in candidate_tokens if len(candidate) >= 5):
            score += 1
    return score
