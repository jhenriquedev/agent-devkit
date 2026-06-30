"""Natural-language prompt runtime for `agent <prompt>`."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from cli.aikit.agent_registry import load_agent_registry
from cli.aikit.agent_executor import execute_plan_tasks
from cli.aikit.capability_runtime import load_agent, run_capability
from cli.aikit.calendar import calendar_summary, calendar_today, calendar_tomorrow
from cli.aikit.control_router import dispatch_natural_control_prompt as route_natural_control_prompt
from cli.aikit.control_router import plan_natural_control_prompt
from cli.aikit.core.requests import AgentPromptRequest
from cli.aikit.errors import DevKitError
from cli.aikit.execution_reviewer import enforce_execution_review
from cli.aikit.github_pr import planned_pr_commands, pr_create_automation, pr_list_review_requests, summarize_pr_list
from cli.aikit.identity import enforce_identity_response, is_identity_question, local_identity_response, public_name
from cli.aikit.llm import invoke_agent_prompt
from cli.aikit.local_llm_operator import enrich_prompt_with_local_result, maybe_delegate_local_llm
from cli.aikit.memory import napkin_context, record_usage
from cli.aikit.model_router import build_model_plan
from cli.aikit.module_controller import run_module_controller
from cli.aikit.orchestrator import attach_source_to_primary_task, build_execution_plan, mark_plan_after_execution, mark_review_task
from cli.aikit.personality import load_personality, update_personality
from cli.aikit.provider_wizard import missing_source_wizard
from cli.aikit.review_gate import build_review_gate
from cli.aikit.router import route_prompt
from cli.aikit.runtime_paths import ROOT
from cli.aikit.sessions import build_contextual_prompt, get_or_create_session, record_exchange
from cli.aikit.setup_wizard_payload import persist_setup_wizard_payload
from cli.aikit.sources import SourceRegistryError, public_source, resolve_source


def effective_dry_run(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "dry_run", False) or getattr(args, "global_dry_run", False))


def parse_rename_prompt(prompt: str) -> str | None:
    text = " ".join(prompt.strip().split())
    patterns = [
        r"(?i)\b(?:mude|troque|altere|renomeie)\s+(?:o\s+)?seu\s+nome\s+para\s+(.+)$",
        r"(?i)\b(?:seu\s+nome\s+agora\s+e|seu\s+nome\s+agora\s+é)\s+(.+)$",
        r"(?i)\b(?:teu\s+nome\s+agora\s+e|teu\s+nome\s+agora\s+é)\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        value = clean_requested_name(match.group(1))
        if value:
            return value
    return None


def clean_requested_name(value: str) -> str | None:
    cleaned = " ".join(value.strip().strip("\"'`.,;:!").split())
    if not cleaned:
        return None
    return cleaned[:80]


def is_capabilities_help_prompt(prompt: str) -> bool:
    normalized = normalize_text(prompt)
    if normalized in {"ajuda", "help", "o que voce faz", "o que voce consegue fazer"}:
        return True
    capability_markers = (
        "o que voce consegue fazer",
        "o que voce pode fazer",
        "como voce pode ajudar",
        "como usar o agent",
        "como usar voce",
        "quais suas capacidades",
        "quais sao suas capacidades",
        "quais agentes voce tem",
        "que agentes voce tem",
    )
    return any(marker in normalized for marker in capability_markers)


def normalize_text(value: str) -> str:
    replacements = str.maketrans(
        {
            "á": "a",
            "à": "a",
            "ã": "a",
            "â": "a",
            "é": "e",
            "ê": "e",
            "í": "i",
            "ó": "o",
            "õ": "o",
            "ô": "o",
            "ú": "u",
            "ç": "c",
        }
    )
    text = value.lower().translate(replacements)
    return " ".join(re.sub(r"[^a-z0-9._:-]+", " ", text).split())


def local_capabilities_help_response(prompt: str, *, name: str) -> dict[str, Any]:
    registry = load_agent_registry(ROOT)
    agents = registry.get("agents") if isinstance(registry.get("agents"), dict) else {}
    capabilities = registry.get("capabilities") if isinstance(registry.get("capabilities"), dict) else {}
    examples = [
        'agent "analise o card 7914 do projeto sustentacao no azure"',
        'agent "mude seu nome para Ianota"',
        "agent onboard minimal",
        "agent catalog search pr",
        "agent mcp tools",
        "agent memory show",
    ]
    response = (
        f"Eu sou {name}. Posso operar como harness/agente local do Agent DevKit: "
        "validar onboarding, lembrar preferencias locais, rotear pedidos para agentes especialistas, "
        "criar wizards de configuracao quando faltar provider/source, executar capabilities deterministicas, "
        "expor ferramentas via MCP, preparar automacoes locais e usar LLMs configuradas quando a tarefa exigir raciocinio aberto. "
        f"Neste runtime encontrei {len(agents)} agentes e {len(capabilities)} capabilities."
    )
    return {
        "kind": "agent",
        "status": "ok",
        "ok": True,
        "requires_llm": False,
        "prompt_received": True,
        "prompt_length": len(prompt),
        "mode": "local-capabilities-help",
        "identity": {"name": name, "source": "local"},
        "response": response,
        "catalog": {
            "agents": len(agents),
            "capabilities": len(capabilities),
        },
        "next_steps": examples,
    }


def embedded_mini_brain_install_response(prompt: str, *, name: str, model_plan: dict[str, Any]) -> dict[str, Any]:
    embedded = (
        ((model_plan.get("mini_brain") or {}).get("embedded") or {})
        if isinstance(model_plan.get("mini_brain"), dict)
        else {}
    )
    status = embedded.get("status") or "not-installed"
    response = (
        f"Eu sou {name}. Consigo orientar o setup inicial localmente, mas o mini-cerebro local ainda nao esta instalado "
        f"(status: {status}). Para habilitar conversa local sem Claude, Codex, Ollama ou API externa, execute "
        "`agent setup mini-brain --yes`. Sem esse download, posso continuar com onboarding, memoria, wizards e "
        "capabilities deterministicas."
    )
    return {
        "kind": "agent",
        "status": "needs-setup",
        "ok": False,
        "requires_llm": False,
        "prompt_received": True,
        "prompt_length": len(prompt),
        "mode": "embedded-mini-brain-not-installed",
        "identity": {"name": name, "source": "local"},
        "llm_backend": "embedded-mini-brain",
        "mini_brain": model_plan.get("mini_brain"),
        "response": response,
        "message": "Embedded mini-brain is not installed yet.",
        "next_steps": [
            "agent setup mini-brain --dry-run",
            "agent setup mini-brain --yes",
            "agent llm configure claude-code --set-default",
            "agent llm configure codex-cli --set-default",
        ],
        "exit_code": 2,
    }


def agent_requires_llm(args: argparse.Namespace) -> dict[str, Any]:
    prompt = " ".join(args.prompt).strip()
    return run_agent_prompt_request(
        AgentPromptRequest(
            prompt=prompt,
            llm=args.llm,
            dry_run=effective_dry_run(args),
            session_id=args.session_id,
            new_session=args.new_session,
            no_llm_fallback=args.no_llm_fallback,
            prog_name=getattr(args, "prog_name", "agent"),
            project=str(Path.cwd()),
        )
    )


def run_agent_prompt_request(request: AgentPromptRequest) -> dict[str, Any]:
    prompt = request.prompt.strip()
    if not prompt:
        raise DevKitError("agent requires a natural-language prompt")
    if request.dry_run:
        return build_agent_dry_run_plan(prompt, request)
    try:
        session = get_or_create_session(
            session_id=request.session_id,
            force_new=request.new_session,
            prompt=prompt,
            project=request.project or str(Path.cwd()),
            backend=request.llm,
        )
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    personality = load_personality()
    name = public_name(personality=personality, invoked_as=request.prog_name)
    rename = parse_rename_prompt(prompt)
    if rename:
        updated = update_personality(agent_name=rename)
        result = {
            "kind": "agent",
            "status": "ok",
            "ok": True,
            "requires_llm": False,
            "prompt_received": True,
            "prompt_length": len(prompt),
            "identity": {"name": updated.get("agent_name"), "source": "local"},
            "action": "rename",
            "response": f"Pronto. Meu nome local agora e {updated.get('agent_name')}.",
        }
        return finalize_agent_session(result, session, prompt, backend=request.llm)
    if is_identity_question(prompt):
        result = {
            "kind": "agent",
            "status": "ok",
            "ok": True,
            "requires_llm": False,
            "prompt_received": True,
            "prompt_length": len(prompt),
            "identity": {"name": name, "source": "local"},
            "response": local_identity_response(prompt, name=name),
        }
        return finalize_agent_session(result, session, prompt, backend=request.llm)
    if is_capabilities_help_prompt(prompt):
        return finalize_agent_session(
            local_capabilities_help_response(prompt, name=name),
            session,
            prompt,
            backend=request.llm,
        )
    natural_result = dispatch_natural_operational_prompt(prompt)
    if natural_result:
        return finalize_agent_session(natural_result, session, prompt, backend=request.llm)
    route = route_prompt(prompt, ROOT)
    if route:
        result = invoke_agentic_route(prompt, route)
        return finalize_agent_session(result, session, prompt, backend=request.llm)
    contextual_prompt = build_contextual_prompt(str(session["id"]), prompt)
    execution_plan = build_execution_plan(ROOT, prompt, dry_run=False)
    routing_decision = execution_plan.get("routing_decision") if isinstance(execution_plan.get("routing_decision"), dict) else {}
    if routing_decision.get("status") in {"ambiguous", "low-confidence"}:
        result = agentic_routing_needs_input_from_plan(prompt, execution_plan)
        return finalize_agent_session(result, session, prompt, backend=request.llm)
    if execution_plan.get("configuration_tasks"):
        result = agentic_needs_input_from_plan(prompt, execution_plan)
        return finalize_agent_session(result, session, prompt, backend=request.llm)
    model_plan = (
        execution_plan.get("model_plan")
        if isinstance(execution_plan.get("model_plan"), dict)
        else build_model_plan(prompt)
    )
    if model_plan.get("strategy") == "human":
        result = agentic_model_strategy_needs_input_from_plan(prompt, execution_plan, model_plan)
        return finalize_agent_session(result, session, prompt, backend=request.llm)
    review_gate = (
        execution_plan.get("review_gate")
        if isinstance(execution_plan.get("review_gate"), dict)
        else build_review_gate(prompt, model_plan=model_plan)
    )
    local_llm_execution = maybe_delegate_local_llm(prompt, model_plan)
    coordinator_prompt = enrich_prompt_with_local_result(contextual_prompt, local_llm_execution)
    requested_backend = request.llm
    if should_prompt_for_embedded_install(model_plan, requested_backend=request.llm):
        result = embedded_mini_brain_install_response(prompt, name=name, model_plan=model_plan)
        return finalize_agent_session(result, session, prompt, backend="embedded-mini-brain")
    if should_use_embedded_coordinator(model_plan, requested_backend=request.llm):
        requested_backend = "embedded-mini-brain"
    result = invoke_agent_prompt(
        coordinator_prompt,
        requested_backend,
        public_name=name,
        allow_fallback=not request.no_llm_fallback,
    )
    review_result = {
        "kind": "execution-review",
        "agent_id": "execution-reviewer",
        "capability_id": "review-final-output",
        "status": "not-run",
        "ok": False,
    }
    if result.get("ok"):
        result, review_gate, review_result = enforce_execution_review(
            prompt=prompt,
            result=result,
            review_gate=review_gate,
            execution_plan=execution_plan,
            producer_backend=str(result.get("llm_backend") or request.llm or ""),
        )
        if review_result.get("ok"):
            execution_plan = mark_review_task(execution_plan, reviewer=str(review_result.get("llm_backend") or "execution-reviewer"))
        elif review_gate.get("status") == "needs-review":
            execution_plan = mark_review_task_needs_review(execution_plan, review_result)
    result["model_plan"] = model_plan
    result["local_llm_execution"] = local_llm_execution
    result["review_gate"] = review_gate
    result["review_result"] = review_result
    result["review_task"] = execution_plan.get("review_task")
    result["execution_plan"] = execution_plan
    result["orchestration_trace"] = execution_plan.get("trace", [])
    result["prompt_length"] = len(prompt)
    result["session_context_applied"] = contextual_prompt != prompt
    result["local_context_applied"] = coordinator_prompt != contextual_prompt
    if result.get("response"):
        result["response"] = enforce_identity_response(str(result["response"]), prompt, name=name)
    result["identity"] = {"name": name, "source": "local"}
    return finalize_agent_session(result, session, prompt, backend=result.get("llm_backend") or request.llm)


def should_use_embedded_coordinator(model_plan: dict[str, Any], *, requested_backend: str | None) -> bool:
    if requested_backend:
        return False
    return (
        model_plan.get("strategy") == "mini-brain"
        and model_plan.get("local_llm_provider") == "embedded-mini-brain"
        and model_plan.get("risk") == "low"
    )


def should_prompt_for_embedded_install(model_plan: dict[str, Any], *, requested_backend: str | None) -> bool:
    if requested_backend:
        return False
    embedded = (
        ((model_plan.get("mini_brain") or {}).get("embedded") or {})
        if isinstance(model_plan.get("mini_brain"), dict)
        else {}
    )
    return (
        model_plan.get("strategy") in {"mini-brain", "external-llm"}
        and model_plan.get("local_llm_provider") == "embedded-mini-brain"
        and embedded.get("available") is not True
        and model_plan.get("fallback") == "configure-local-mini-brain-or-use-external-llm"
    )


def mark_review_task_needs_review(execution_plan: dict[str, Any], review_result: dict[str, Any]) -> dict[str, Any]:
    task = dict(execution_plan.get("review_task") or {})
    if task:
        task["status"] = "needs-review"
        task["reviewer"] = None
        task["message"] = review_result.get("message")
        execution_plan["review_task"] = task
    return execution_plan


def agentic_needs_input_from_plan(prompt: str, execution_plan: dict[str, Any]) -> dict[str, Any]:
    configuration_task = next(
        (task for task in execution_plan.get("configuration_tasks") or [] if isinstance(task, dict)),
        {},
    )
    wizard = configuration_task.get("setup_wizard") if isinstance(configuration_task.get("setup_wizard"), dict) else {}
    provider = configuration_task.get("provider") or wizard.get("provider")
    payload = {
        "kind": "agent",
        "status": "needs-input",
        "ok": False,
        "mode": "agentic-plan",
        "prompt_received": True,
        "prompt_length": len(prompt),
        "provider": provider,
        "source_provider": provider,
        "requires_source": True,
        "execution_plan": execution_plan,
        "orchestration_trace": execution_plan.get("trace", []),
        "setup_wizard": wizard,
        "next_question": wizard.get("next_question"),
        "message": wizard.get("message") or "O plano multiagente precisa de configuracao antes de executar.",
        "next_steps": [
            "Responda a pergunta do wizard para autorizar ou negar a configuracao deste provider.",
            "Depois de configurar a fonte, reexecute ou retome o mesmo prompt.",
        ],
        "exit_code": 2,
    }
    return persist_setup_wizard_payload(payload, execution_plan=execution_plan)


def agentic_routing_needs_input_from_plan(prompt: str, execution_plan: dict[str, Any]) -> dict[str, Any]:
    routing_decision = execution_plan.get("routing_decision") if isinstance(execution_plan.get("routing_decision"), dict) else {}
    payload = {
        "kind": "agent",
        "status": "needs-input",
        "ok": False,
        "mode": "agentic-routing",
        "prompt_received": True,
        "prompt_length": len(prompt),
        "requires_routing_confirmation": True,
        "routing_decision": routing_decision,
        "matches": routing_decision.get("candidates") or [],
        "execution_plan": execution_plan,
        "orchestration_trace": execution_plan.get("trace", []),
        "message": "O roteamento do prompt ficou ambiguo ou com baixa confianca.",
        "next_steps": [
            "Confirme qual agente/capability deve tratar o pedido ou reformule o prompt com mais contexto.",
            "Use `agent --dry-run \"...\"` para inspecionar candidatos sem executar.",
        ],
        "exit_code": 2,
    }
    return payload


def agentic_model_strategy_needs_input_from_plan(
    prompt: str,
    execution_plan: dict[str, Any],
    model_plan: dict[str, Any],
) -> dict[str, Any]:
    execution_plan["status"] = "needs-input"
    execution_plan["model_plan"] = model_plan
    trace = list(execution_plan.get("trace") or [])
    trace.append({"agent_id": "task-orchestrator", "action": "model-strategy", "status": "waiting-for-human"})
    execution_plan["trace"] = trace
    return {
        "kind": "agent",
        "status": "needs-input",
        "ok": False,
        "mode": "model-strategy",
        "prompt_received": True,
        "prompt_length": len(prompt),
        "requires_human_confirmation": True,
        "model_plan": model_plan,
        "execution_plan": execution_plan,
        "orchestration_trace": execution_plan.get("trace", []),
        "message": model_plan.get("reason") or "A politica de modelo exige confirmacao humana antes de executar.",
        "next_steps": [
            "Confirme explicitamente a acao permitida ou reformule o pedido removendo decisoes destrutivas/sensiveis.",
            "Use `agent --dry-run \"...\"` para inspecionar a estrategia e os gates sem executar.",
        ],
        "exit_code": 2,
    }


def dispatch_natural_operational_prompt(prompt: str) -> dict[str, Any] | None:
    normalized = " ".join(prompt.lower().split())
    control_result = dispatch_natural_control_prompt(normalized)
    if control_result:
        control_result["prompt_received"] = True
        control_result["prompt_length"] = len(prompt)
        return control_result
    if "agenda" in normalized:
        if "amanha" in normalized or "amanhã" in normalized:
            payload = calendar_tomorrow()
        else:
            payload = calendar_today()
        payload = dict(payload)
        payload["kind"] = "agent"
        payload["mode"] = "calendar-route"
        payload["requires_llm"] = False
        payload["prompt_received"] = True
        payload["prompt_length"] = len(prompt)
        payload["response"] = calendar_summary(payload)
        if payload.get("status") == "needs-input":
            payload["ok"] = False
        else:
            payload["ok"] = True
        return payload
    if has_pr_intent(normalized):
        if any(marker in normalized for marker in ("diariamente", "todo dia", "diaria", "diária", "recorrente")):
            payload = pr_create_automation()
            return {
                "kind": "agent",
                "status": payload.get("status"),
                "ok": True,
                "mode": "pr-automation-route",
                "requires_llm": False,
                "prompt_received": True,
                "prompt_length": len(prompt),
                "response": "Automacao diaria de revisao de PRs criada em modo report-only.",
                "result": payload,
            }
        payload = pr_list_review_requests()
        return {
            "kind": "agent",
            "status": payload.get("status"),
            "ok": payload.get("status") == "ok",
            "mode": "pr-route",
            "requires_llm": False,
            "prompt_received": True,
            "prompt_length": len(prompt),
            "response": summarize_pr_list(payload),
            "result": payload,
            "exit_code": payload.get("exit_code", 0 if payload.get("status") == "ok" else 2),
        }
    return None


def dispatch_natural_control_prompt(normalized_prompt: str) -> dict[str, Any] | None:
    return route_natural_control_prompt(ROOT, normalized_prompt)


def build_agent_dry_run_plan(prompt: str, request: AgentPromptRequest) -> dict[str, Any]:
    normalized = " ".join(prompt.lower().split())
    control_plan = plan_natural_control_prompt(ROOT, normalized)
    if control_plan:
        control_plan["prompt_received"] = True
        control_plan["prompt_length"] = len(prompt)
        return control_plan
    route = route_prompt(prompt, ROOT)
    execution_plan = build_execution_plan(ROOT, prompt, dry_run=True)
    model_plan = (
        execution_plan.get("model_plan")
        if isinstance(execution_plan.get("model_plan"), dict)
        else build_model_plan(prompt, route=route)
    )
    review_gate = execution_plan.get("review_gate") if isinstance(execution_plan.get("review_gate"), dict) else build_review_gate(prompt, route=route, model_plan=model_plan)
    plan: dict[str, Any] = {
        "kind": "agent",
        "status": "planned",
        "ok": True,
        "dry_run": True,
        "requires_llm": False,
        "prompt_received": True,
        "prompt_length": len(prompt),
        "mode": "dry-run",
        "intent": "llm" if not route else route.get("intent"),
        "route": route,
        "llm_backend": request.llm,
        "external_writes": False,
        "providers": {"used": [], "missing": [], "skipped": []},
        "commands": [],
        "permissions": [],
        "model_plan": model_plan,
        "review_gate": review_gate,
        "execution_plan": execution_plan,
        "orchestration_trace": execution_plan.get("trace", []),
        "response": "Dry-run: nenhuma chamada LLM ou escrita externa foi executada.",
    }
    routing_decision = execution_plan.get("routing_decision") if isinstance(execution_plan.get("routing_decision"), dict) else {}
    if routing_decision.get("status") in {"ambiguous", "low-confidence"}:
        plan["requires_routing_confirmation"] = True
        plan["routing_decision"] = routing_decision
        plan["matches"] = routing_decision.get("candidates") or []
        plan["response"] = "Dry-run: o roteamento precisa de confirmacao antes de executar."
    if "agenda" in normalized:
        plan.update(
            {
                "intent": "calendar",
                "mode": "calendar-dry-run",
                "providers": {"used": ["calendar"], "missing": [], "skipped": []},
                "data_reads": ["configured calendar provider, if present"],
                "response": "Dry-run: o calendario seria consultado localmente se configurado.",
            }
        )
        return plan
    if has_pr_intent(normalized):
        recurring = any(marker in normalized for marker in ("diariamente", "todo dia", "diaria", "diária", "recorrente"))
        plan.update(
            {
                "intent": "github-pr-review",
                "mode": "pr-dry-run",
                "providers": {"used": ["github"], "missing": [], "skipped": []},
                "commands": planned_pr_commands("list-review-requests"),
                "external_writes": False,
                "permissions": [{"agent": "github-pr-reviewer", "provider": "github", "required_level": "read-only"}],
                "response": (
                    "Dry-run: a automacao diaria de PR seria planejada em modo report-only."
                    if recurring
                    else "Dry-run: PRs aguardando revisao seriam listadas via gh em modo report-only."
                ),
            }
        )
        return plan
    if route:
        plan["providers"] = {"used": [route.get("provider")], "missing": [], "skipped": []}
        plan["response"] = "Dry-run: a capability roteada seria executada somente apos validar source/provider."
        return plan
    if not plan.get("requires_routing_confirmation"):
        plan["response"] = "Dry-run: o prompt exigiria LLM configurada; nenhuma chamada foi feita."
    return plan


def has_pr_intent(normalized_prompt: str) -> bool:
    tokens = {token.strip(".,;:!?()[]{}\"'") for token in normalized_prompt.split()}
    return bool({"pr", "prs"} & tokens) or "pull request" in normalized_prompt or "pull requests" in normalized_prompt


def finalize_agent_session(
    result: dict[str, Any],
    session: dict[str, Any],
    prompt: str,
    *,
    backend: str | None = None,
) -> dict[str, Any]:
    try:
        result["session"] = record_exchange(str(session["id"]), prompt=prompt, result=result, backend=backend)
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    return result


def invoke_agentic_route(prompt: str, route: dict[str, Any]) -> dict[str, Any]:
    execution_plan = build_execution_plan(ROOT, prompt, dry_run=False)
    try:
        source = resolve_source(
            provider=route.get("provider"),
            intent=route.get("intent"),
            agent_id=route.get("agent_id"),
        )
    except SourceRegistryError as exc:
        raise DevKitError(str(exc)) from exc

    if not source:
        wizard = missing_source_wizard(prompt, route, root=ROOT)
        if execution_plan.get("configuration_tasks"):
            execution_plan["configuration_tasks"][0]["setup_wizard"] = wizard
        execution_plan["status"] = "needs-input"
        execution_plan["trace"] = [
            {"agent_id": "task-orchestrator", "action": "plan", "status": "needs-input"},
            {"agent_id": "provider-configurator", "action": "configure", "status": "waiting-for-user"},
        ]
        payload = {
            "kind": "agent",
            "status": "needs-input",
            "ok": False,
            "requires_source": True,
            "provider": route.get("provider"),
            "source_provider": route.get("provider"),
            "prompt_received": True,
            "prompt_length": len(prompt),
            "route": route,
            "napkin": napkin_context(ROOT, agent_id=route.get("agent_id")),
            "execution_plan": execution_plan,
            "orchestration_trace": execution_plan.get("trace", []),
            "setup_wizard": wizard,
            "next_question": wizard.get("next_question"),
            "message": wizard.get("message"),
            "next_steps": [
                "Responda a pergunta do wizard para autorizar ou negar a configuracao desta fonte.",
                "Se preferir teste local, configure uma source com fixture sem armazenar segredos.",
                "O prompt original sera retomado apos a fonte reutilizavel ser configurada.",
            ],
            "exit_code": 2,
        }
        return persist_setup_wizard_payload(payload, execution_plan=execution_plan, route=route)

    model_plan = execution_plan.get("model_plan") if isinstance(execution_plan.get("model_plan"), dict) else build_model_plan(prompt, route=route)
    if model_plan.get("strategy") == "human":
        payload = agentic_model_strategy_needs_input_from_plan(prompt, execution_plan, model_plan)
        payload["route"] = route
        payload["source"] = public_source(source)
        return payload

    execution_plan = attach_source_to_primary_task(execution_plan)
    def run_prompt_capability(agent: dict[str, Any], capability_id: str, capability_args: list[str]) -> dict[str, Any]:
        return run_capability(
            agent,
            capability_id,
            capability_args,
            capture_output=True,
            origin="agent-prompt",
        )

    if execution_plan.get("controller_enabled"):
        controller_run = run_module_controller(
            execution_plan,
            load_agent=load_agent,
            run_capability=run_prompt_capability,
        )
        execution_plan["module_controller_run"] = controller_run
        execution_plan["shared_context"] = controller_run.get("shared_context") or execution_plan.get("shared_context")
        executed = list(controller_run.get("executed_tasks") or [])
        blocked = list(controller_run.get("blocked_tasks") or [])
    else:
        executed, blocked = execute_plan_tasks(
            execution_plan,
            load_agent=load_agent,
            run_capability=run_prompt_capability,
        )
    execution_plan = mark_plan_after_execution(execution_plan, executed, blocked)
    result = (executed[0].get("result") if executed else blocked[0].get("result") if blocked and isinstance(blocked[0].get("result"), dict) else {}) or {}
    response = result.get("stdout") or result.get("error") or ""
    record_usage(prompt, route=route, source_id=str(source["id"]))
    review_gate = execution_plan.get("review_gate") if isinstance(execution_plan.get("review_gate"), dict) else build_review_gate(prompt, route=route, model_plan=model_plan)
    review_payload = {
        "kind": "agent",
        "status": execution_plan.get("status") if execution_plan.get("status") != "partial" else result.get("status"),
        "ok": bool(executed) and not blocked,
        "response": response,
    }
    review_result = {
        "kind": "execution-review",
        "agent_id": "execution-reviewer",
        "capability_id": "review-final-output",
        "status": "not-run",
        "ok": False,
    }
    if result.get("ok"):
        review_payload, review_gate, review_result = enforce_execution_review(
            prompt=prompt,
            result=review_payload,
            review_gate=review_gate,
            execution_plan=execution_plan,
            producer_backend="deterministic-capability",
        )
        if review_result.get("ok"):
            execution_plan = mark_review_task(execution_plan, reviewer=str(review_result.get("llm_backend") or "execution-reviewer"))
        elif review_gate.get("status") == "needs-review":
            execution_plan = mark_review_task_needs_review(execution_plan, review_result)
    return {
        "kind": "agent",
        "status": review_payload.get("status"),
        "ok": bool(review_payload.get("ok")),
        "mode": "agentic-route",
        "legacy_mode": "deterministic-route",
        "prompt_received": True,
        "prompt_length": len(prompt),
        "route": route,
        "source": public_source(source),
        "napkin": napkin_context(ROOT, agent_id=route.get("agent_id"), source_id=str(source["id"])),
        "model_plan": model_plan,
        "review_gate": review_gate,
        "review_result": review_result,
        "review_task": execution_plan.get("review_task"),
        "execution_plan": execution_plan,
        "orchestration_trace": execution_plan.get("trace", []),
        "response": review_payload.get("response") or response,
        "result": result,
        "exit_code": review_payload.get("exit_code", result.get("exit_code", 0 if executed and not blocked else 1)),
    }
