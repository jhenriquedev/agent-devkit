"""Multi-agent planning for natural-language Agent DevKit prompts."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from cli.aikit.agent_registry import find_capability, load_agent_registry
from cli.aikit.autonomy import build_autonomy_contract
from cli.aikit.collaboration import build_collaboration_graph, initial_shared_context, normalize_collaborative_task
from cli.aikit.configuration_orchestrator import provider_setup_wizard
from cli.aikit.memory import redact_secrets
from cli.aikit.model_router import build_model_plan
from cli.aikit.review_gate import build_review_gate
from cli.aikit.router import route_prompt
from cli.aikit.sources import SourceRegistryError, public_source, resolve_source
from cli.aikit.write_policy import normalize_write_policy, write_policy_public_fields


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
ROUTING_SELECTED_THRESHOLD = 3
ROUTING_AMBIGUITY_DELTA = 1


def build_execution_plan(root: Path, prompt: str, *, dry_run: bool = False) -> dict[str, Any]:
    registry = load_agent_registry(root)
    safe_prompt = redact_secrets(prompt)
    route = route_prompt(prompt, root=root)
    routing_decision = decide_routing(registry, prompt, route)
    domain_agent = select_domain_agent(registry, prompt, route, routing_decision)
    specialist_tasks = specialist_tasks_for_prompt(registry, prompt, route, domain_agent, routing_decision)
    configuration_tasks = configuration_tasks_for(registry, root, prompt, route, specialist_tasks, dry_run=dry_run)
    model_plan = build_model_plan(
        prompt,
        route=route,
        routing_decision=routing_decision,
        specialist_tasks=specialist_tasks,
        configuration_tasks=configuration_tasks,
    )
    model_plan = attach_local_llm_agent_contract(registry, model_plan)
    review_gate = build_review_gate(prompt, route=route, model_plan=model_plan)
    review = review_task(registry, review_gate)
    review = attach_review_dependencies(review, specialist_tasks)
    collaboration_enabled = bool(specialist_tasks or configuration_tasks or review.get("required"))
    collaboration_graph = build_collaboration_graph(specialist_tasks, configuration_tasks, review)
    module_controller = module_controller_contract(domain_agent, specialist_tasks)
    execution_model = execution_model_contract(domain_agent, review_gate, module_controller, model_plan)
    policy_summary = policy_summary_for_plan(specialist_tasks, configuration_tasks, review)
    autonomy_contract = build_autonomy_contract(
        model_plan=model_plan,
        routing_decision=routing_decision,
        specialist_tasks=specialist_tasks,
        configuration_tasks=configuration_tasks,
        review_gate=review_gate,
        execution_model=execution_model,
        policy_summary=policy_summary,
        collaboration_enabled=collaboration_enabled,
        controller_enabled=bool(module_controller.get("enabled")),
    )
    execution_model = attach_autonomy_to_execution_model(execution_model, autonomy_contract)
    status = "needs-input" if configuration_tasks and not dry_run else "planned"
    if routing_decision.get("status") in {"ambiguous", "low-confidence"} and not dry_run:
        status = "needs-input"
    if model_plan.get("strategy") == "human" and not dry_run:
        status = "needs-input"
    return {
        "kind": "agentic-execution-plan",
        "schema_version": "ai-devkit.agentic-plan/v1",
        "status": status,
        "dry_run": dry_run,
        "prompt": safe_prompt,
        "coordinator_agent": runtime_agent_by_role(registry, "coordinator", fallback=RUNTIME_COORDINATOR),
        "domain_agent": domain_agent,
        "route": route,
        "routing_decision": routing_decision,
        "model_plan": model_plan,
        "review_gate": review_gate,
        "specialist_tasks": specialist_tasks,
        "configuration_tasks": configuration_tasks,
        "review_task": review,
        "collaboration_enabled": collaboration_enabled,
        "collaboration_graph": collaboration_graph,
        "shared_context": initial_shared_context(safe_prompt, routing_decision),
        "execution_model": execution_model,
        "autonomy_contract": autonomy_contract,
        "stop_conditions": execution_model["stop_conditions"],
        "module_controller": module_controller,
        "controller_enabled": bool(module_controller.get("enabled")),
        "policy_summary": policy_summary,
        "executed_tasks": [],
        "blocked_tasks": [],
        "trace": trace_for_plan(
            specialist_tasks,
            configuration_tasks,
            status=status,
            coordinator_agent_id=runtime_agent_id(registry, "coordinator", RUNTIME_COORDINATOR["id"]),
        ),
    }


def select_domain_agent(
    registry: dict[str, Any],
    prompt: str,
    route: dict[str, Any] | None,
    routing_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = normalize(prompt)
    agents = registry.get("agents") or {}
    if re.search(r"\bn1\b|primeiro nivel|1o nivel|1º nivel", normalized) and "n1-support-agent" in agents:
        return slim_agent(agents["n1-support-agent"])
    if re.search(r"\bn2\b|segundo nivel|2o nivel|2º nivel", normalized) and "n2-support-agent" in agents:
        return slim_agent(agents["n2-support-agent"])
    if route and route.get("agent_id") in agents:
        return slim_agent(agents[str(route["agent_id"])])
    if routing_decision and routing_decision.get("status") in {"ambiguous", "low-confidence"}:
        return runtime_agent_by_role(registry, "coordinator", fallback=RUNTIME_COORDINATOR)
    if routing_decision and routing_decision.get("status") == "selected":
        selected_agent_id = str(routing_decision.get("selected_agent_id") or "")
        if selected_agent_id in agents:
            return slim_agent(agents[selected_agent_id])
    return runtime_agent_by_role(registry, "coordinator", fallback=RUNTIME_COORDINATOR)


def specialist_tasks_for_prompt(
    registry: dict[str, Any],
    prompt: str,
    route: dict[str, Any] | None,
    domain_agent: dict[str, Any],
    routing_decision: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if routing_decision and routing_decision.get("status") in {"ambiguous", "low-confidence"}:
        return []
    if domain_agent.get("id") in {"n1-support-agent", "n2-support-agent"}:
        return orchestrated_tasks(registry, str(domain_agent["id"]), prompt, route)
    if route:
        task = task_from_route(registry, route)
        return [task] if task else []
    if routing_decision and routing_decision.get("status") == "selected":
        selected_agent_id = routing_decision.get("selected_agent_id")
        selected_capability_id = routing_decision.get("selected_capability_id")
        if selected_agent_id and selected_capability_id:
            capability = find_capability(registry, str(selected_agent_id), str(selected_capability_id))
            if capability:
                task = base_task(capability, prompt=prompt)
                task["primary"] = True
                task["selection"] = {
                    "method": routing_decision.get("method"),
                    "score": routing_decision.get("score"),
                }
                return [task]
    if domain_agent.get("id") and not is_runtime_agent(registry, str(domain_agent["id"])):
        task = best_capability_task(registry, str(domain_agent["id"]), prompt)
        return [task] if task else []
    return []


def orchestrated_tasks(registry: dict[str, Any], agent_id: str, prompt: str, route: dict[str, Any] | None) -> list[dict[str, Any]]:
    agent = (registry.get("agents") or {}).get(agent_id) or {}
    tasks: list[dict[str, Any]] = []
    previous_task_id: str | None = None
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
            task["critical"] = True
        task = normalize_collaborative_task(
            task,
            role=collaboration_role_for_task(task),
            depends_on=[previous_task_id] if previous_task_id else [],
            sequence=len(tasks) + 1,
        )
        tasks.append(task)
        previous_task_id = str(task.get("task_id") or task.get("id"))
    if route and not any(task.get("primary") for task in tasks):
        routed = task_from_route(registry, route)
        if routed:
            routed["primary"] = True
            routed["critical"] = True
            tasks.insert(0, normalize_collaborative_task(routed, role=collaboration_role_for_task(routed), sequence=0))
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


def decide_routing(registry: dict[str, Any], prompt: str, route: dict[str, Any] | None) -> dict[str, Any]:
    support_agent_id = support_level_agent_id(registry, prompt)
    if support_agent_id:
        return enrich_routing_decision(
            {
                "status": "selected",
                "method": "support-level-regex",
                "selected_agent_id": support_agent_id,
                "selected_capability_id": None,
                "confidence": 0.98,
                "score": None,
                "candidates": [
                    {
                        "agent_id": support_agent_id,
                        "score": None,
                        "matched_anchors": [],
                        "matched_intents": ["support.level"],
                        "selected_capability_id": None,
                        "legacy_fallback": False,
                    }
                ],
            },
            prompt=prompt,
        )
    if route:
        return enrich_routing_decision(
            {
                "status": "deterministic",
                "method": "deterministic-regex",
                "selected_agent_id": route.get("agent_id"),
                "selected_capability_id": route.get("capability_id"),
                "confidence": 1.0,
                "score": None,
                "candidates": [
                    {
                        "agent_id": route.get("agent_id"),
                        "capability_id": route.get("capability_id"),
                        "score": None,
                        "matched_anchors": [route.get("intent")],
                        "matched_intents": [route.get("intent")],
                        "selected_capability_id": route.get("capability_id"),
                        "legacy_fallback": False,
                    }
                ],
            },
            prompt=prompt,
        )

    candidates = routing_candidates(registry, prompt)
    if not candidates:
        return enrich_routing_decision(
            {
                "status": "no-match",
                "method": "manifest-routing",
                "selected_agent_id": None,
                "selected_capability_id": None,
                "confidence": 0.0,
                "score": 0,
                "candidates": [],
            },
            prompt=prompt,
        )

    top = candidates[0]
    second = candidates[1] if len(candidates) > 1 else None
    method = "legacy-fallback" if top.get("legacy_fallback") else "manifest-routing"
    if int(top["score"]) < ROUTING_SELECTED_THRESHOLD:
        status = "low-confidence"
        selected_agent_id = None
        selected_capability_id = None
        confidence = 0.35
    elif second and int(top["score"]) - int(second["score"]) <= ROUTING_AMBIGUITY_DELTA:
        status = "ambiguous"
        selected_agent_id = None
        selected_capability_id = None
        confidence = 0.5
    else:
        status = "selected"
        selected_agent_id = top.get("agent_id")
        selected_capability_id = top.get("selected_capability_id")
        confidence = routing_confidence(int(top["score"]))

    return enrich_routing_decision(
        {
            "status": status,
            "method": method,
            "selected_agent_id": selected_agent_id,
            "selected_capability_id": selected_capability_id,
            "confidence": confidence,
            "score": top.get("score"),
            "candidates": candidates[:5],
        },
        prompt=prompt,
    )


def enrich_routing_decision(decision: dict[str, Any], *, prompt: str) -> dict[str, Any]:
    result = dict(decision)
    candidates = [item for item in result.get("candidates") or [] if isinstance(item, dict)]
    result["confidence_label"] = routing_confidence_label(result.get("confidence"))
    result["entities"] = extract_routing_entities(prompt)
    result["alternatives"] = routing_alternatives(candidates, selected_agent_id=result.get("selected_agent_id"))
    result["requires_confirmation"] = result.get("status") in {"ambiguous", "low-confidence"}
    result["reason"] = routing_reason(result, candidates)
    if result["requires_confirmation"]:
        result["question"] = routing_confirmation_question(result, candidates)
        result["options"] = routing_confirmation_options(candidates)
    else:
        result["question"] = None
        result["options"] = []
    return result


def routing_confidence_label(confidence: Any) -> str:
    try:
        value = float(confidence)
    except (TypeError, ValueError):
        return "low"
    if value >= 0.75:
        return "high"
    if value >= 0.5:
        return "medium"
    return "low"


def routing_reason(decision: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    status = decision.get("status")
    method = decision.get("method")
    if status == "deterministic":
        return "Prompt matched a deterministic route with explicit entities."
    if status == "no-match":
        return "No manifest routing candidate matched enough prompt signals."
    if status == "low-confidence":
        top = candidates[0] if candidates else {}
        return f"Best routing candidate {top.get('agent_id') or '-'} scored below the selection threshold."
    if status == "ambiguous":
        names = ", ".join(str(item.get("agent_id")) for item in candidates[:2] if item.get("agent_id"))
        return f"Multiple routing candidates scored too closely: {names or '-'}."
    if status == "selected":
        top = candidates[0] if candidates else {}
        agent = decision.get("selected_agent_id") or top.get("agent_id") or "-"
        capability = decision.get("selected_capability_id") or top.get("selected_capability_id")
        capability_text = f" and capability {capability}" if capability else ""
        signals = routing_candidate_signal_text(top)
        return f"Selected {agent}{capability_text} via {method} using {signals}."
    return "Routing decision was produced by the planner."


def routing_candidate_signal_text(candidate: dict[str, Any]) -> str:
    signals: list[str] = []
    for field, label in (
        ("matched_anchors", "anchors"),
        ("matched_keywords", "keywords"),
        ("matched_domains", "domains"),
        ("matched_aliases", "aliases"),
        ("matched_intents", "intents"),
        ("matched_examples", "examples"),
        ("selected_capability_matched_anchors", "capability anchors"),
        ("selected_capability_matched_keywords", "capability keywords"),
        ("selected_capability_matched_entities", "capability entities"),
        ("selected_capability_matched_aliases", "capability aliases"),
        ("selected_capability_matched_intents", "capability intents"),
        ("selected_capability_matched_examples", "capability examples"),
    ):
        values = candidate.get(field) or []
        if values:
            signals.append(f"{label}: {', '.join(str(item) for item in values[:3])}")
    return "; ".join(signals) if signals else "score overlap"


def routing_alternatives(candidates: list[dict[str, Any]], *, selected_agent_id: Any) -> list[dict[str, Any]]:
    alternatives = []
    for candidate in candidates:
        if candidate.get("agent_id") == selected_agent_id:
            continue
        alternatives.append(
            {
                "agent_id": candidate.get("agent_id"),
                "capability_id": candidate.get("selected_capability_id"),
                "score": candidate.get("score"),
                "reason": routing_candidate_signal_text(candidate),
            }
        )
    return alternatives[:4]


def routing_confirmation_question(decision: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    if decision.get("status") == "low-confidence":
        return "Qual agente ou capability deve tratar este pedido?"
    names = ", ".join(str(item.get("agent_id")) for item in candidates[:3] if item.get("agent_id"))
    return f"Qual destes agentes deve tratar este pedido: {names or 'nenhum candidato claro'}?"


def routing_confirmation_options(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    options = []
    for candidate in candidates[:5]:
        options.append(
            {
                "agent_id": candidate.get("agent_id"),
                "capability_id": candidate.get("selected_capability_id"),
                "score": candidate.get("score"),
                "reason": routing_candidate_signal_text(candidate),
            }
        )
    return options


def extract_routing_entities(prompt: str) -> dict[str, Any]:
    entities: dict[str, Any] = {}
    card_match = re.search(r"\b(?:card|cartao|tarefa|work\s*item)\s*#?(\d{2,})\b", prompt, re.IGNORECASE)
    if card_match:
        entities["card_id"] = card_match.group(1)
    pr_match = re.search(r"\b(?:pr|pull\s+request)\s*#?(\d+)\b", prompt, re.IGNORECASE)
    if pr_match:
        entities["pr_id"] = pr_match.group(1)
    return entities


def support_level_agent_id(registry: dict[str, Any], prompt: str) -> str | None:
    normalized = normalize(prompt)
    agents = registry.get("agents") or {}
    if re.search(r"\bn1\b|primeiro nivel|1o nivel|1º nivel", normalized) and "n1-support-agent" in agents:
        return "n1-support-agent"
    if re.search(r"\bn2\b|segundo nivel|2o nivel|2º nivel", normalized) and "n2-support-agent" in agents:
        return "n2-support-agent"
    return None


def routing_candidates(registry: dict[str, Any], prompt: str) -> list[dict[str, Any]]:
    prompt_tokens = expanded_tokens(prompt)
    normalized_prompt = normalize(prompt)
    candidates: list[dict[str, Any]] = []
    for agent in (registry.get("agents") or {}).values():
        if not isinstance(agent, dict):
            continue
        agent_id = str(agent.get("id") or "")
        if is_runtime_agent(registry, agent_id):
            continue
        routing = routing_profile(agent)
        anchors = set(routing.get("anchors") or [])
        keywords = set(routing.get("keywords") or [])
        domains = set(routing.get("domains") or [])
        aliases = set(routing.get("aliases") or [])
        has_declared_routing = bool(
            anchors
            or keywords
            or domains
            or aliases
            or routing.get("intents")
            or routing.get("examples")
        )
        matched_anchors = sorted(matched_routing_anchors(anchors, prompt_tokens, normalized_prompt))
        matched_keywords = sorted(matched_routing_anchors(keywords, prompt_tokens, normalized_prompt))
        matched_domains = sorted(matched_routing_anchors(domains, prompt_tokens, normalized_prompt))
        matched_aliases = sorted(matched_routing_anchors(aliases, prompt_tokens, normalized_prompt))
        matched_intents = sorted(matched_routing_intents(routing.get("intents") or [], prompt_tokens, normalized_prompt))
        matched_examples = sorted(matched_routing_examples(routing.get("examples") or [], normalized_prompt))
        capability_match = best_capability_route_match(agent, prompt)
        if has_declared_routing and not (
            matched_anchors
            or matched_keywords
            or matched_domains
            or matched_aliases
            or matched_intents
            or matched_examples
            or capability_match
        ):
            continue
        agent_tokens = expanded_tokens(
            " ".join(
                [
                    agent_id,
                    str(agent.get("name") or ""),
                    str(agent.get("purpose") or ""),
                    " ".join(str(item) for item in anchors),
                    " ".join(str(item) for item in keywords),
                    " ".join(str(item) for item in domains),
                    " ".join(str(item) for item in aliases),
                    " ".join(str(item) for item in routing.get("intents") or []),
                    " ".join(str(item) for item in routing.get("examples") or []),
                ]
            )
        )
        score = weighted_overlap(prompt_tokens, agent_tokens)
        score += 3 * len(matched_anchors)
        score += 2 * len(matched_keywords)
        score += 2 * len(matched_domains)
        score += 2 * len(matched_aliases)
        score += 2 * len(matched_intents)
        score += 2 * len(matched_examples)
        try:
            score += int(routing.get("priority") or 0) // 50
        except (TypeError, ValueError):
            pass
        if capability_match:
            score += int(capability_match["score"])
        if score <= 0:
            continue
        candidates.append(
            {
                "agent_id": agent_id,
                "score": score,
                "matched_anchors": matched_anchors,
                "matched_keywords": matched_keywords,
                "matched_domains": matched_domains,
                "matched_aliases": matched_aliases,
                "matched_intents": matched_intents,
                "matched_examples": matched_examples,
                "selected_capability_id": (capability_match or {}).get("capability_id"),
                "selected_capability_score": (capability_match or {}).get("score"),
                "selected_capability_matched_anchors": (capability_match or {}).get("matched_anchors", []),
                "selected_capability_matched_keywords": (capability_match or {}).get("matched_keywords", []),
                "selected_capability_matched_entities": (capability_match or {}).get("matched_entities", []),
                "selected_capability_matched_aliases": (capability_match or {}).get("matched_aliases", []),
                "selected_capability_matched_intents": (capability_match or {}).get("matched_intents", []),
                "selected_capability_matched_examples": (capability_match or {}).get("matched_examples", []),
                "legacy_fallback": False,
            }
        )
    candidates.sort(key=lambda item: (-int(item["score"]), str(item["agent_id"])))
    return candidates


def best_capability_route_match(agent: dict[str, Any], prompt: str) -> dict[str, Any] | None:
    capabilities = [item for item in (agent.get("capabilities_index") or {}).values() if isinstance(item, dict)]
    prompt_tokens = expanded_tokens(prompt)
    normalized_prompt = normalize(prompt)
    best: dict[str, Any] | None = None
    for capability in capabilities:
        routing = routing_profile(capability)
        anchors = set(routing.get("anchors") or [])
        keywords = set(routing.get("keywords") or [])
        entities = set(routing.get("entities") or [])
        aliases = set(routing.get("aliases") or [])
        if not (anchors or keywords or entities or aliases or routing.get("intents") or routing.get("examples")):
            continue
        matched_anchors = sorted(matched_routing_anchors(anchors, prompt_tokens, normalized_prompt))
        matched_keywords = sorted(matched_routing_anchors(keywords, prompt_tokens, normalized_prompt))
        matched_entities = sorted(matched_routing_anchors(entities, prompt_tokens, normalized_prompt))
        matched_aliases = sorted(matched_routing_anchors(aliases, prompt_tokens, normalized_prompt))
        matched_intents = sorted(matched_routing_intents(routing.get("intents") or [], prompt_tokens, normalized_prompt))
        matched_examples = sorted(matched_routing_examples(routing.get("examples") or [], normalized_prompt))
        if not (
            matched_anchors
            or matched_keywords
            or matched_entities
            or matched_aliases
            or matched_intents
            or matched_examples
        ):
            continue
        capability_tokens = expanded_tokens(
            " ".join(
                [
                    str(capability.get("short_id") or ""),
                    str(capability.get("name") or ""),
                    str(capability.get("purpose") or ""),
                    " ".join(str(item) for item in anchors),
                    " ".join(str(item) for item in keywords),
                    " ".join(str(item) for item in entities),
                    " ".join(str(item) for item in aliases),
                    " ".join(str(item) for item in routing.get("intents") or []),
                    " ".join(str(item) for item in routing.get("examples") or []),
                ]
            )
        )
        score = weighted_overlap(prompt_tokens, capability_tokens)
        score += 3 * len(matched_anchors)
        score += 2 * len(matched_keywords)
        score += 2 * len(matched_entities)
        score += 2 * len(matched_aliases)
        score += 2 * len(matched_intents)
        score += 2 * len(matched_examples)
        try:
            score += int(routing.get("priority") or 0) // 50
        except (TypeError, ValueError):
            pass
        if score <= 0:
            continue
        candidate = {
            "capability_id": capability.get("short_id"),
            "score": score,
            "matched_anchors": matched_anchors,
            "matched_keywords": matched_keywords,
            "matched_entities": matched_entities,
            "matched_aliases": matched_aliases,
            "matched_intents": matched_intents,
            "matched_examples": matched_examples,
        }
        if best is None or int(candidate["score"]) > int(best["score"]):
            best = candidate
    return best


def matched_routing_anchors(anchors: set[str], prompt_tokens: set[str], normalized_prompt: str) -> set[str]:
    matched: set[str] = set()
    for anchor in anchors:
        normalized_anchor = normalize(str(anchor))
        if not normalized_anchor:
            continue
        anchor_tokens = expanded_tokens(normalized_anchor)
        if anchor_tokens & prompt_tokens or (len(normalized_anchor) >= 5 and normalized_anchor in normalized_prompt):
            matched.add(str(anchor))
    return matched


def matched_routing_intents(intents: list[Any], prompt_tokens: set[str], normalized_prompt: str) -> set[str]:
    matched: set[str] = set()
    for intent in intents:
        text = normalize(str(intent))
        if not text:
            continue
        intent_tokens = expanded_tokens(text.replace(".", " ").replace("-", " "))
        if intent_tokens and intent_tokens <= prompt_tokens:
            matched.add(str(intent))
        elif len(text) >= 5 and text in normalized_prompt:
            matched.add(str(intent))
    return matched


def matched_routing_examples(examples: list[Any], normalized_prompt: str) -> set[str]:
    matched: set[str] = set()
    raw_prompt_tokens = routing_text_tokens(normalized_prompt)
    for example in examples:
        text = normalize(str(example))
        if not text:
            continue
        example_tokens = routing_text_tokens(text)
        meaningful_tokens = example_tokens - STOP_WORDS
        raw_overlap = meaningful_tokens & raw_prompt_tokens
        if raw_overlap and len(raw_overlap) >= max(3, min(5, len(meaningful_tokens) // 2)):
            matched.add(str(example))
        elif len(text) >= 8 and text in normalized_prompt:
            matched.add(str(example))
    return matched


def routing_text_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9._-]*", normalize(value))
        if len(token) >= 3 and token not in STOP_WORDS
    }


def routing_profile(item: dict[str, Any]) -> dict[str, Any]:
    routing = item.get("routing") if isinstance(item.get("routing"), dict) else {}
    return routing if isinstance(routing, dict) else {}


def routing_confidence(score: int) -> float:
    return round(max(0.05, min(0.95, score / 12)), 2)


def best_capability_task(registry: dict[str, Any], agent_id: str, prompt: str) -> dict[str, Any] | None:
    agent = (registry.get("agents") or {}).get(agent_id) or {}
    capabilities = [item for item in (agent.get("capabilities_index") or {}).values() if isinstance(item, dict)]
    if not capabilities:
        return None
    route_match = best_capability_route_match(agent, prompt)
    if route_match:
        capability_id = route_match.get("capability_id")
        capability = next((item for item in capabilities if item.get("short_id") == capability_id), None)
        if capability:
            task = base_task(capability, prompt=prompt)
            task["primary"] = True
            task["selection"] = {"method": "manifest-routing", "score": route_match.get("score")}
            return task
    hinted = hinted_capability(capabilities, prompt)
    if hinted:
        task = base_task(hinted, prompt=prompt)
        task["primary"] = True
        task["selection"] = {"method": "legacy-hint", "score": None}
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
    task = {
        "id": f"{capability['agent_id']}.{capability['short_id']}",
        "agent_id": capability["agent_id"],
        "capability_id": capability["short_id"],
        "capability": capability["id"],
        "purpose": capability.get("purpose"),
        "write_policy": normalize_write_policy(capability.get("write_policy")),
        "write_policy_metadata": write_policy_public_fields(capability.get("write_policy"))["write_policy_metadata"],
        "provider": infer_provider(capability),
        "args": [],
        "entities": {},
        "status": "planned",
        "executable": bool(capability.get("has_runner")),
        "prompt": redact_secrets(prompt),
        "primary": False,
    }
    return normalize_collaborative_task(task, role=collaboration_role_for_task(task))


def collaboration_role_for_task(task: dict[str, Any]) -> str:
    agent_id = str(task.get("agent_id") or "")
    capability_id = str(task.get("capability_id") or "")
    if agent_id == PROVIDER_CONFIGURATOR_AGENT_ID:
        return "coordinator"
    if agent_id == REVIEWER_AGENT_ID or capability_id.startswith("review"):
        return "reviewer"
    if capability_id.startswith(("read", "search", "list", "inspect", "load", "extract", "collect", "trace", "find")):
        return "collector"
    if capability_id.startswith(("update", "move", "comment", "assign", "attach", "register")):
        return "coordinator"
    return "analyzer"


def policy_summary_for_plan(
    specialist_tasks: list[dict[str, Any]],
    configuration_tasks: list[dict[str, Any]],
    review: dict[str, Any],
) -> dict[str, Any]:
    tasks = [*specialist_tasks, *configuration_tasks]
    if review:
        tasks.append(review)
    summary = {
        "total_tasks": len(tasks),
        "autonomous_safe": 0,
        "requires_confirmation": 0,
        "blocked_by_default": 0,
        "unknown": 0,
        "policies": {},
    }
    for task in tasks:
        metadata = task.get("write_policy_metadata") if isinstance(task.get("write_policy_metadata"), dict) else {}
        policy = str(metadata.get("canonical") or task.get("write_policy") or "unknown")
        summary["policies"][policy] = int(summary["policies"].get(policy, 0)) + 1
        if metadata.get("known") is False:
            summary["unknown"] += 1
        if metadata.get("autonomous_safe"):
            summary["autonomous_safe"] += 1
        if metadata.get("requires_confirmation"):
            summary["requires_confirmation"] += 1
        if metadata.get("blocked_by_default"):
            summary["blocked_by_default"] += 1
    return summary


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
    provider_configurator_id = runtime_agent_id(registry, "provider-configurator", PROVIDER_CONFIGURATOR_AGENT_ID)
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
        capability = find_capability(registry, provider_configurator_id, "configure-provider-source") or {}
        wizard = provider_setup_wizard(root, provider, prompt=prompt, route=route, reason="Provider/source required by multi-agent plan.")
        result.append(
            normalize_collaborative_task(
                {
                    "id": f"{provider_configurator_id}.{provider}",
                    "agent_id": provider_configurator_id,
                    "capability_id": "configure-provider-source",
                    "capability": capability.get("id") or f"{provider_configurator_id}.configure-provider-source",
                    "purpose": capability.get("purpose"),
                    "write_policy": normalize_write_policy(capability.get("write_policy"), default="local_config_write"),
                    "write_policy_metadata": write_policy_public_fields(
                        capability.get("write_policy"),
                        default="local_config_write",
                    )["write_policy_metadata"],
                    "path": capability.get("path"),
                    "provider": provider,
                    "status": "waiting-for-user",
                    "setup_wizard": wizard,
                },
                role="coordinator",
                sequence=len(result),
            )
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
    controller_run = plan.get("module_controller_run") if isinstance(plan.get("module_controller_run"), dict) else {}
    if controller_run.get("status") == "needs-input":
        plan["status"] = "needs-input"
        plan["human_escalations"] = list(controller_run.get("human_escalations") or [])
    elif blocked and not executed:
        plan["status"] = "blocked"
    elif blocked and executed:
        plan["status"] = "partial"
    elif executed:
        plan["status"] = "ok"
    coordinator = plan.get("coordinator_agent") if isinstance(plan.get("coordinator_agent"), dict) else {}
    plan["trace"] = trace_for_plan(
        plan.get("specialist_tasks") or [],
        plan.get("configuration_tasks") or [],
        executed=executed,
        blocked=blocked,
        status=plan["status"],
        coordinator_agent_id=str(coordinator.get("id") or RUNTIME_COORDINATOR["id"]),
    )
    return plan


def review_task(registry: dict[str, Any], review_gate: dict[str, Any]) -> dict[str, Any]:
    reviewer_agent_id = runtime_agent_id(registry, "reviewer", REVIEWER_AGENT_ID)
    capability = find_capability(registry, reviewer_agent_id, "review-final-output") or {}
    task = {
        "id": f"{reviewer_agent_id}.review-final-output",
        "agent_id": reviewer_agent_id,
        "capability_id": "review-final-output",
        "capability": capability.get("id") or f"{reviewer_agent_id}.review-final-output",
        "purpose": capability.get("purpose"),
        "write_policy": normalize_write_policy(capability.get("write_policy")),
        "write_policy_metadata": write_policy_public_fields(capability.get("write_policy"))["write_policy_metadata"],
        "path": capability.get("path"),
        "status": "pending" if review_gate.get("required") else "not-required",
        "required": bool(review_gate.get("required")),
        "preferred_reviewers": list(review_gate.get("preferred_reviewers") or []),
    }
    return normalize_collaborative_task(task, role="reviewer")


def attach_review_dependencies(review: dict[str, Any], specialist_tasks: list[dict[str, Any]]) -> dict[str, Any]:
    dependencies = [
        str(task.get("task_id") or task.get("id"))
        for task in specialist_tasks
        if isinstance(task, dict) and (task.get("task_id") or task.get("id"))
    ]
    return normalize_collaborative_task(review, role="reviewer", depends_on=dependencies)


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
    coordinator_agent_id: str = RUNTIME_COORDINATOR["id"],
) -> list[dict[str, Any]]:
    trace = [{"agent_id": coordinator_agent_id, "action": "plan", "status": status}]
    trace.extend(trace_task(task, action="delegate-config") for task in configuration_tasks)
    trace.extend(trace_task(task, action="delegate") for task in specialist_tasks)
    trace.extend(trace_result(item, action="handoff") for item in executed or [])
    trace.extend(trace_result(item, action="blocked") for item in blocked or [])
    return trace


def trace_task(task: dict[str, Any], *, action: str) -> dict[str, Any]:
    return {
        "task_id": task.get("task_id") or task.get("id"),
        "agent_id": task["agent_id"],
        "capability_id": task.get("capability_id"),
        "role": task.get("role"),
        "depends_on": list(task.get("depends_on") or []),
        "action": action,
        "status": task.get("status"),
    }


def trace_result(item: dict[str, Any], *, action: str) -> dict[str, Any]:
    return {
        "task_id": item.get("task_id") or item.get("id"),
        "agent_id": item["agent_id"],
        "capability_id": item.get("capability_id"),
        "role": item.get("role"),
        "action": action,
        "status": item.get("status"),
    }


def infer_provider(capability: dict[str, Any]) -> str | None:
    if capability.get("provider"):
        return str(capability["provider"])
    runtime = capability.get("runtime") if isinstance(capability.get("runtime"), dict) else {}
    if runtime.get("provider"):
        return str(runtime["provider"])
    integration = capability.get("integration") if isinstance(capability.get("integration"), dict) else {}
    if integration.get("provider"):
        return str(integration["provider"])
    requires = capability.get("requires") if isinstance(capability.get("requires"), dict) else {}
    providers = requires.get("providers") if isinstance(requires.get("providers"), list) else []
    if providers and isinstance(providers[0], dict):
        return str(providers[0].get("id") or "") or None
    return None


def attach_local_llm_agent_contract(registry: dict[str, Any], model_plan: dict[str, Any]) -> dict[str, Any]:
    plan = dict(model_plan)
    local_llm_agent_id = runtime_agent_id(registry, "local-worker", LOCAL_LLM_OPERATOR_AGENT_ID)
    agent = (registry.get("agents") or {}).get(local_llm_agent_id)
    select_capability = find_capability(registry, local_llm_agent_id, "select-local-worker") or {}
    delegate_capability = find_capability(registry, local_llm_agent_id, "delegate-operational-task") or {}
    plan["operator_agent"] = slim_agent(agent) if isinstance(agent, dict) else {
        "id": local_llm_agent_id,
        "name": "Local LLM Operator",
        "kind": "runtime-agent",
    }
    plan["selection_capability"] = {
        "agent_id": local_llm_agent_id,
        "capability_id": "select-local-worker",
        "capability": select_capability.get("id") or f"{local_llm_agent_id}.select-local-worker",
    }
    plan["delegation_capability"] = {
        "agent_id": local_llm_agent_id,
        "capability_id": "delegate-operational-task",
        "capability": delegate_capability.get("id") or f"{local_llm_agent_id}.delegate-operational-task",
    }
    return plan


def runtime_agent_by_role(registry: dict[str, Any], role: str, *, fallback: dict[str, Any]) -> dict[str, Any]:
    return runtime_agent(registry, runtime_agent_id(registry, role, str(fallback.get("id") or "")), fallback=fallback)


def runtime_agent_id(registry: dict[str, Any], role: str, fallback_agent_id: str) -> str:
    runtime_roles = registry.get("runtime_roles") if isinstance(registry.get("runtime_roles"), dict) else {}
    return str(runtime_roles.get(role) or fallback_agent_id)


def is_runtime_agent(registry: dict[str, Any], agent_id: str) -> bool:
    agent = (registry.get("agents") or {}).get(agent_id)
    if not isinstance(agent, dict):
        return agent_id in {RUNTIME_COORDINATOR["id"], REVIEWER_AGENT_ID, PROVIDER_CONFIGURATOR_AGENT_ID, LOCAL_LLM_OPERATOR_AGENT_ID}
    return agent.get("kind") == "runtime-agent" or bool(agent.get("runtime_role"))


def runtime_agent(registry: dict[str, Any], agent_id: str, *, fallback: dict[str, Any]) -> dict[str, Any]:
    agent = (registry.get("agents") or {}).get(agent_id)
    if isinstance(agent, dict):
        public = slim_agent(agent)
        runtime_role = agent.get("runtime_role") if isinstance(agent.get("runtime_role"), dict) else {}
        public["role"] = runtime_role.get("kind") or fallback.get("role")
        return public
    return dict(fallback)


def slim_agent(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": agent.get("id"),
        "name": agent.get("name"),
        "kind": agent.get("kind") or "specialist-agent",
        "purpose": agent.get("purpose"),
        "path": agent.get("path"),
        "agent_mode": agent.get("agent_mode") if isinstance(agent.get("agent_mode"), dict) else {},
    }


def module_controller_contract(domain_agent: dict[str, Any], specialist_tasks: list[dict[str, Any]]) -> dict[str, Any]:
    mode = domain_agent.get("agent_mode") if isinstance(domain_agent.get("agent_mode"), dict) else {}
    if not mode:
        return {"enabled": False, "reason": "agent-mode-not-declared"}
    planned_capabilities = [
        f"{task.get('agent_id')}/{task.get('capability_id')}"
        for task in specialist_tasks
        if isinstance(task, dict) and task.get("agent_id") and task.get("capability_id")
    ]
    return {
        "enabled": True,
        "agent_id": domain_agent.get("id"),
        "mode": mode,
        "limits": {
            "max_steps": mode.get("max_steps"),
            "max_specialists": mode.get("max_specialists"),
            "max_llm_calls": mode.get("max_llm_calls"),
            "timeout_seconds": mode.get("timeout_seconds"),
            "external_writes": mode.get("external_writes"),
            "can_call_llm": mode.get("can_call_llm"),
        },
        "allowed_capabilities": list(mode.get("allowed_capabilities") or []),
        "planned_capabilities": planned_capabilities,
        "stop_conditions": list(mode.get("stop_conditions") or []),
    }


def execution_model_contract(
    domain_agent: dict[str, Any],
    review_gate: dict[str, Any],
    module_controller: dict[str, Any],
    model_plan: dict[str, Any],
) -> dict[str, Any]:
    mode = domain_agent.get("agent_mode") if isinstance(domain_agent.get("agent_mode"), dict) else {}
    stop_conditions = list(mode.get("stop_conditions") or module_controller.get("stop_conditions") or [])
    if not stop_conditions:
        stop_conditions = ["success", "needs-input", "blocked", "max-steps"]
    max_llm_calls = resolve_model_limited_llm_calls(mode.get("max_llm_calls"), model_plan.get("max_llm_calls"))
    return {
        "schema_version": "ai-devkit.execution-model/v1",
        "decision_owner": "agent-devkit-core",
        "coordinator": "task-orchestrator",
        "domain_agent": domain_agent.get("id"),
        "review_required": bool(review_gate.get("required")),
        "model_strategy": model_plan.get("strategy"),
        "model_risk": model_plan.get("risk"),
        "model_confidence": model_plan.get("confidence"),
        "model_reason": model_plan.get("reason"),
        "model_fallback": model_plan.get("fallback"),
        "limits": {
            "max_steps": mode.get("max_steps") or 1,
            "max_specialists": mode.get("max_specialists") or 1,
            "max_llm_calls": max_llm_calls if max_llm_calls is not None else 0,
            "timeout_seconds": mode.get("timeout_seconds") or 300,
        },
        "allowed_side_effects": {
            "external_writes": mode.get("external_writes") is True,
            "can_call_capabilities": mode.get("can_call_capabilities") is True,
            "can_call_llm": False if max_llm_calls == 0 else mode.get("can_call_llm"),
        },
        "human_escalation_policy": {
            "on_low_confidence": True,
            "on_conflict": True,
            "on_high_risk": True,
            "on_reviewer_block": True,
            "on_policy_block": True,
        },
        "stop_conditions": stop_conditions,
    }


def attach_autonomy_to_execution_model(
    execution_model: dict[str, Any],
    autonomy_contract: dict[str, Any],
) -> dict[str, Any]:
    model = dict(execution_model)
    model["autonomy_level"] = autonomy_contract.get("level")
    model["autonomy_level_id"] = autonomy_contract.get("level_id")
    model["autonomy_status"] = autonomy_contract.get("status")
    model["execution_allowed"] = autonomy_contract.get("execution_allowed") is True
    model["requires_human"] = autonomy_contract.get("requires_human") is True
    model["requires_review"] = autonomy_contract.get("requires_review") is True
    return model


def resolve_model_limited_llm_calls(mode_limit: Any, model_limit: Any) -> int:
    limits: list[int] = []
    for value in (mode_limit, model_limit):
        if value is None:
            continue
        try:
            limits.append(max(0, int(value)))
        except (TypeError, ValueError):
            continue
    return min(limits) if limits else 0


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
