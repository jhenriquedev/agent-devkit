"""Runtime execution for the local-llm-operator agent."""

from __future__ import annotations

from typing import Any

from cli.aikit.llm import invoke_agent_prompt
from cli.aikit.memory import redact_secrets


FORBIDDEN_DELEGATION_MARKERS = (
    "aprove",
    "aprovar",
    "reprove",
    "reprovar",
    "deploy",
    "delete",
    "excluir",
    "execute escrita",
    "permissao",
    "permissão",
)


def maybe_delegate_local_llm(prompt: str, model_plan: dict[str, Any]) -> dict[str, Any]:
    """Execute a bounded operational task with Ollama when the model plan selected it."""
    delegation = model_plan.get("delegation") if isinstance(model_plan.get("delegation"), dict) else {}
    if not model_plan.get("local_llm_selected") or not delegation.get("selected"):
        return skipped("not-selected", "Local LLM delegation was not selected for this prompt.", model_plan=model_plan)
    lowered = prompt.lower()
    if any(marker in lowered for marker in FORBIDDEN_DELEGATION_MARKERS):
        return skipped("forbidden", "Prompt contains an action that local LLM workers cannot execute.", model_plan=model_plan)
    delegated_prompt = build_delegated_prompt(prompt, model_plan)
    result = invoke_agent_prompt(
        delegated_prompt,
        "ollama",
        public_name="Local LLM Operator",
        allow_fallback=False,
    )
    payload = {
        "kind": "local-llm-execution",
        "agent_id": "local-llm-operator",
        "capability_id": "delegate-operational-task",
        "capability": "local-llm-operator.delegate-operational-task",
        "status": "ok" if result.get("ok") else result.get("status", "failed"),
        "ok": bool(result.get("ok")),
        "llm_backend": result.get("llm_backend"),
        "model_provider": "ollama",
        "delegated_prompt": redact_secrets(delegated_prompt),
        "response": result.get("response"),
        "result": sanitize_llm_result(result),
        "requires_review": True,
    }
    if not result.get("ok"):
        payload["message"] = result.get("message") or "Local LLM delegation failed."
    return payload


def build_delegated_prompt(prompt: str, model_plan: dict[str, Any]) -> str:
    forbidden = ", ".join((model_plan.get("delegation") or {}).get("forbidden_actions") or [])
    return "\n".join(
        [
            "Execute apenas a parte operacional da tarefa abaixo.",
            "Nao tome decisao final, nao aprove, nao escreva externamente e nao revise a entrega final.",
            f"Acoes proibidas: {forbidden}.",
            "Retorne um resumo estruturado, evidencias extraidas, lacunas e confianca.",
            "",
            "Tarefa original:",
            redact_secrets(prompt),
        ]
    )


def enrich_prompt_with_local_result(prompt: str, local_execution: dict[str, Any]) -> str:
    if not local_execution.get("ok") or not local_execution.get("response"):
        return prompt
    return "\n".join(
        [
            prompt,
            "",
            "Contexto operacional produzido pelo local-llm-operator/Ollama:",
            str(local_execution["response"]),
            "",
            "Use esse contexto apenas como apoio. A decisao, resposta final e revisao continuam sob responsabilidade do coordenador.",
        ]
    )


def skipped(reason: str, message: str, *, model_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "local-llm-execution",
        "agent_id": "local-llm-operator",
        "capability_id": "delegate-operational-task",
        "capability": "local-llm-operator.delegate-operational-task",
        "status": "skipped",
        "ok": False,
        "reason": reason,
        "message": message,
        "model_provider": model_plan.get("local_llm_provider") or "ollama",
        "requires_review": bool(model_plan.get("local_llm_recommended") or model_plan.get("local_llm_selected")),
    }


def sanitize_llm_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": result.get("status"),
        "ok": result.get("ok"),
        "llm_backend": result.get("llm_backend"),
        "llm_backend_attempts": result.get("llm_backend_attempts"),
        "message": result.get("message"),
        "exit_code": result.get("exit_code"),
    }
