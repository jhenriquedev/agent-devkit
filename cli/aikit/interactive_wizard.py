"""Interactive setup wizard flow for CLI TTY sessions."""

from __future__ import annotations

import sys
from typing import Any

from cli.aikit.core.requests import AgentPromptRequest
from cli.aikit.core.runtime import run_agent_prompt
from cli.aikit.wizard_state import WizardStateError, answer_wizard, cancel_wizard, show_wizard


def maybe_run_interactive_wizard(result: dict[str, Any]) -> dict[str, Any]:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return result
    wizard = result.get("setup_wizard") if isinstance(result.get("setup_wizard"), dict) else None
    if not wizard or not wizard.get("wizard_id") or result.get("status") != "needs-input":
        return result
    print(result.get("message") or "O agente precisa de configuracao antes de continuar.")
    return run_interactive_wizard(str(wizard["wizard_id"]))


def run_interactive_wizard(wizard_id: str) -> dict[str, Any]:
    payload = show_wizard(wizard_id)
    while True:
        wizard = payload.get("wizard") if isinstance(payload.get("wizard"), dict) else {}
        question = payload.get("next_question") or wizard.get("next_question")
        if not isinstance(question, dict):
            return payload
        print_interactive_question(question)
        try:
            answer = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return cancel_wizard(wizard_id, reason="interactive wizard interrupted")
        if answer.strip().lower() in {"cancelar", "cancel", "sair", "exit"}:
            return cancel_wizard(wizard_id, reason="interactive wizard cancelled by user")
        try:
            payload = answer_wizard(wizard_id, answer)
        except WizardStateError as exc:
            print(f"Erro: {exc}")
            continue
        if payload.get("status") == "completed":
            resume_prompt = payload.get("resume_prompt") or (payload.get("wizard") or {}).get("resume_prompt")
            if resume_prompt:
                payload["resumed_prompt"] = True
                payload["resume_result"] = resume_agent_prompt(str(resume_prompt))
            else:
                payload["resumed_prompt"] = False
            return payload
        if payload.get("status") in {"cancelled", "denied-by-user", "failed"}:
            payload.setdefault("resumed_prompt", False)
            return payload


def print_interactive_question(question: dict[str, Any]) -> None:
    text = question.get("text") or "Informe a resposta."
    print(f"\nPergunta: {text}")
    if question.get("type") == "confirm":
        print("[s/N]")
    options = question.get("options")
    if isinstance(options, list) and options:
        print("Opcoes: " + ", ".join(str(item) for item in options))
    if question.get("suggested_value"):
        print(f"Sugestao: {question['suggested_value']}")
    if question.get("env_ref_key"):
        print("Informe o nome da variavel de ambiente, nao o valor da credencial.")
    print("Digite 'cancelar' para interromper.")


def resume_agent_prompt(prompt: str) -> dict[str, Any]:
    result = run_agent_prompt(
        AgentPromptRequest(
            prompt=prompt,
            prog_name="agent",
        )
    )
    result.pop("audit", None)
    return result
