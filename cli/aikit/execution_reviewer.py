"""Runtime execution for the execution-reviewer agent."""

from __future__ import annotations

from typing import Any

from cli.aikit.llm import BACKENDS, candidate_backend_ids, doctor_backend, invoke_agent_prompt, load_config
from cli.aikit.review_gate import mark_reviewed


PREFERRED_REVIEW_BACKENDS = ("claude-code", "codex-cli")
REVIEW_OK_MARKER = "REVIEW OK"
REVIEW_BLOCKED_MARKER = "REVIEW BLOCKED"


def enforce_execution_review(
    *,
    prompt: str,
    result: dict[str, Any],
    review_gate: dict[str, Any],
    execution_plan: dict[str, Any] | None = None,
    producer_backend: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Run a second concrete review when required and apply the gate outcome."""
    if not review_gate.get("required"):
        review_result = {
            "kind": "execution-review",
            "agent_id": "execution-reviewer",
            "capability_id": "review-final-output",
            "status": "not-required",
            "ok": True,
        }
        return result, review_gate, review_result

    response = str(result.get("response") or result.get("message") or "")
    review_backend = select_review_backend(producer_backend=producer_backend, preferred=review_gate.get("preferred_reviewers") or [])
    if not review_backend:
        review_result = needs_review("No configured independent reviewer backend is available.", producer_backend=producer_backend)
        return block_for_review(result, review_gate, review_result)

    review_prompt = build_review_prompt(prompt=prompt, response=response, review_gate=review_gate, execution_plan=execution_plan)
    invoked = invoke_agent_prompt(
        review_prompt,
        review_backend,
        public_name="Execution Reviewer",
        allow_fallback=False,
    )
    decision = parse_review_decision(str(invoked.get("response") or ""))
    review_result = {
        "kind": "execution-review",
        "agent_id": "execution-reviewer",
        "capability_id": "review-final-output",
        "capability": "execution-reviewer.review-final-output",
        "status": review_status(invoked=invoked, decision=decision),
        "ok": bool(invoked.get("ok")) and decision == "approved",
        "llm_backend": invoked.get("llm_backend"),
        "producer_backend": producer_backend,
        "decision": decision,
        "response": invoked.get("response"),
        "message": invoked.get("message"),
        "attempts": invoked.get("llm_backend_attempts"),
    }
    if not invoked.get("ok"):
        return block_for_review(result, review_gate, review_result)
    if decision == "blocked":
        review_result["message"] = "Execution reviewer blocked the proposed final output."
        return block_for_review(result, review_gate, review_result)
    if decision != "approved":
        review_result["message"] = "Execution reviewer did not return REVIEW OK."
        return block_for_review(result, review_gate, review_result)
    reviewed_gate = mark_reviewed(review_gate, reviewer=str(invoked.get("llm_backend") or review_backend), notes=str(invoked.get("response") or "Reviewed."))
    return result, reviewed_gate, review_result


def select_review_backend(*, producer_backend: str | None, preferred: list[str]) -> str | None:
    config = load_config()
    candidates = candidate_backend_ids(config=config, allow_fallback=True)
    preferred_order = [item for item in list(preferred or []) + list(PREFERRED_REVIEW_BACKENDS) if item in BACKENDS]
    ordered = [item for item in preferred_order if item in candidates]
    ordered.extend(item for item in candidates if item not in ordered and item != "ollama")
    for backend_id in ordered:
        if backend_id == producer_backend:
            continue
        backend = doctor_backend(BACKENDS[backend_id], config)
        if backend.get("status") == "ok":
            return backend_id
    return None


def build_review_prompt(
    *,
    prompt: str,
    response: str,
    review_gate: dict[str, Any],
    execution_plan: dict[str, Any] | None,
) -> str:
    plan_summary = {}
    if isinstance(execution_plan, dict):
        plan_summary = {
            "status": execution_plan.get("status"),
            "coordinator": (execution_plan.get("coordinator_agent") or {}).get("id") if isinstance(execution_plan.get("coordinator_agent"), dict) else None,
            "specialist_tasks": [
                {
                    "agent_id": task.get("agent_id"),
                    "capability_id": task.get("capability_id"),
                    "status": task.get("status"),
                }
                for task in execution_plan.get("specialist_tasks") or []
                if isinstance(task, dict)
            ],
        }
    return "\n".join(
        [
            "Revise a entrega final do Agent DevKit antes da conclusao.",
            "Verifique aderencia ao pedido, riscos, lacunas, evidencias, uso indevido de credenciais e necessidade de bloquear.",
            "Responda com uma decisao objetiva: REVIEW OK ou REVIEW BLOCKED, seguida de justificativa curta.",
            "",
            f"Motivo do review gate: {review_gate.get('reason')}",
            f"Prompt original: {prompt}",
            f"Resumo do plano: {plan_summary}",
            "",
            "Resposta final proposta:",
            response,
        ]
    )


def parse_review_decision(response: str) -> str:
    upper = response.upper()
    if REVIEW_BLOCKED_MARKER in upper:
        return "blocked"
    if REVIEW_OK_MARKER in upper:
        return "approved"
    return "unstructured"


def review_status(*, invoked: dict[str, Any], decision: str) -> str:
    if not invoked.get("ok"):
        return str(invoked.get("status", "failed"))
    if decision == "blocked":
        return "blocked"
    if decision != "approved":
        return "needs-review"
    return "ok"


def needs_review(message: str, *, producer_backend: str | None) -> dict[str, Any]:
    return {
        "kind": "execution-review",
        "agent_id": "execution-reviewer",
        "capability_id": "review-final-output",
        "capability": "execution-reviewer.review-final-output",
        "status": "needs-review",
        "ok": False,
        "producer_backend": producer_backend,
        "message": message,
    }


def block_for_review(
    result: dict[str, Any],
    review_gate: dict[str, Any],
    review_result: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    blocked = dict(result)
    blocked["status"] = "needs-review"
    blocked["ok"] = False
    blocked["exit_code"] = 2
    blocked["message"] = review_result.get("message") or "Execution requires review before completion."
    gate = dict(review_gate)
    gate["status"] = "needs-review"
    gate["reviewer"] = None
    gate["notes"] = review_result.get("message")
    return blocked, gate, review_result
