"""Interactive setup wizard flow for CLI TTY sessions."""

from __future__ import annotations

import sys
from typing import Any

from cli.aikit.core.requests import AgentPromptRequest
from cli.aikit.core.runtime import run_agent_prompt
from cli.aikit.llm import BACKENDS, configure_backend
from cli.aikit.mini_brain import DEFAULT_OLLAMA_MODEL, setup_mini_brain
from cli.aikit.ollama import ollama_status
from cli.aikit.onboarding import onboarding_status
from cli.aikit.personality import load_personality, update_personality
from cli.aikit.runtime_paths import ROOT
from cli.aikit.wizard_state import WizardStateError, answer_wizard, cancel_wizard, show_wizard


def maybe_run_interactive_wizard(result: dict[str, Any]) -> dict[str, Any]:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return result
    if result.get("kind") == "onboarding" and result.get("status") != "ready":
        return run_interactive_onboarding(result)
    if result.get("kind") == "personality" and result.get("status") == "needs-input":
        print(result.get("message") or "Vou configurar nome, usuario e estilo local.")
        configure_personality_interactively(result)
        return load_personality()
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


def run_interactive_onboarding(result: dict[str, Any]) -> dict[str, Any]:
    agent = result.get("agent") if isinstance(result.get("agent"), dict) else {}
    print(f"{agent.get('name') or 'Agent DevKit'} iniciado.")
    print("Vou revisar o estado local e pedir apenas o que for necessario.")
    mode = choose_onboarding_mode()
    if mode == "skip":
        print("Onboarding pulado por agora.")
        return result
    if ask_yes_no("Deseja configurar nome, usuario e estilo agora?", default=True):
        configure_personality_interactively(agent)

    fresh = onboarding_status(ROOT)
    llm = fresh.get("llm") if isinstance(fresh.get("llm"), dict) else {}
    if int(llm.get("usable_count") or 0) < 1:
        configure_llm_interactively()

    fresh = onboarding_status(ROOT)
    ollama = fresh.get("ollama") if isinstance(fresh.get("ollama"), dict) else {}
    if ollama.get("status") == "missing":
        install_plan = ollama.get("install_plan") if isinstance(ollama.get("install_plan"), dict) else {}
        command = install_plan.get("command")
        print("\nOllama nao foi encontrado.")
        if command:
            print(f"Instalacao sugerida: {command}")
        print("Depois de instalar, rode `agent setup mini-brain --yes` para baixar o Qwen3-0.6B.")
    elif ask_yes_no(f"Deseja habilitar o mini cerebro local com {DEFAULT_OLLAMA_MODEL}?", default=False):
        set_default = ask_yes_no("Usar este mini cerebro como backend LLM padrao?", default=False)
        setup = setup_mini_brain(yes=True, set_default=set_default)
        print(setup.get("message") or f"Mini cerebro: {setup.get('status')}")

    fresh = onboarding_status(ROOT)
    toolchain = fresh.get("toolchain") if isinstance(fresh.get("toolchain"), dict) else {}
    optional_missing = toolchain.get("optional_missing") or []
    if optional_missing:
        print("\nFerramentas opcionais ausentes: " + ", ".join(str(item) for item in optional_missing))
        print("Para revisar instalacoes com opt-in: agent toolchain doctor")
        if mode == "complete" and ask_yes_no("Deseja abrir o plano de toolchain agora?", default=False):
            print("Rode: agent toolchain install all --dry-run")
    if mode == "complete":
        print("\nOnboarding completo tambem pode revisar sources, notificacoes, knowledge e memoria compartilhada sob demanda:")
        print("- agent source list")
        print("- agent notifications doctor")
        print("- agent knowledge doctor")
        print("- agent shared-memory list")
    return onboarding_status(ROOT)


def choose_onboarding_mode() -> str:
    print("\nModos de onboarding:")
    print("1. minimo: identidade, coordenador LLM, mini-cerebro local e memoria")
    print("2. completo: minimo + toolchain, sources, notificacoes, knowledge e memorias")
    print("3. pular")
    answer = ask_text("Escolha o modo", default="minimo").strip().lower()
    if answer in {"1", "minimo", "mínimo", "minimal"}:
        return "minimal"
    if answer in {"2", "completo", "complete", "full"}:
        return "complete"
    if answer in {"3", "pular", "skip", "cancelar", "cancel"}:
        return "skip"
    return "minimal"


def configure_personality_interactively(agent: dict[str, Any]) -> None:
    current_name = str(agent.get("name") or "Agent DevKit")
    current_tone = str(agent.get("tone") or "direct")
    current_detail = str(agent.get("detail_level") or "concise")
    agent_name = ask_text("Como devo me chamar?", default=current_name)
    user_name = ask_text("Como voce se chama?", default=str(agent.get("user_name") or ""))
    language = ask_text("Idioma padrao das respostas?", default=str(agent.get("language") or "pt-BR"))
    tone = ask_text("Tom das respostas?", default=current_tone)
    detail_level = ask_text("Nivel de detalhe?", default=current_detail)
    update_personality(
        agent_name=agent_name,
        user_name=user_name,
        language=language,
        tone=tone,
        detail_level=detail_level,
    )


def configure_llm_interactively() -> None:
    print("\nNenhum backend LLM coordenador utilizavel foi detectado.")
    print("Opcoes: claude-code, codex-cli, ollama, openai, anthropic, openrouter, pular")
    choice = ask_text("Qual backend deseja configurar primeiro?", default="pular").strip().lower()
    if choice in {"", "pular", "skip", "cancelar", "cancel"}:
        print("Configuracao de LLM pulada por agora.")
        return
    if choice not in BACKENDS:
        print(f"Backend desconhecido: {choice}")
        return
    if choice in {"claude-code", "codex-cli"}:
        configure_backend(choice, set_default=True)
        print(f"{choice} registrado como backend padrao. A autenticacao continua no CLI oficial.")
        return
    if choice == "ollama":
        status = ollama_status()
        if status.get("status") != "ok":
            install_plan = status.get("install_plan") if isinstance(status.get("install_plan"), dict) else {}
            print("Ollama ainda nao esta instalado.")
            if install_plan.get("command"):
                print(f"Instalacao sugerida: {install_plan['command']}")
            return
        configure_backend("ollama", model=DEFAULT_OLLAMA_MODEL, set_default=True)
        print("Ollama registrado como backend padrao.")
        return
    env_default = BACKENDS[choice].api_key_env or ""
    api_key_env = ask_text("Nome da variavel de ambiente da API key?", default=env_default)
    model = ask_text("Modelo padrao?", default=BACKENDS[choice].default_model or "")
    configure_backend(choice, api_key_env=api_key_env, model=model, set_default=True)
    print(f"{choice} registrado sem armazenar segredo; a chave deve existir em ${api_key_env}.")


def ask_yes_no(question: str, *, default: bool) -> bool:
    suffix = "[S/n]" if default else "[s/N]"
    answer = ask_text(f"{question} {suffix}", default="sim" if default else "nao").strip().lower()
    if answer in {"s", "sim", "y", "yes", "true", "1", "ok"}:
        return True
    if answer in {"n", "nao", "não", "no", "false", "0"}:
        return False
    return default


def ask_text(question: str, *, default: str = "") -> str:
    prompt = f"{question}"
    if default:
        prompt += f" ({default})"
    prompt += "\n> "
    try:
        answer = input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    value = " ".join(answer.split())
    return value or default


def resume_agent_prompt(prompt: str) -> dict[str, Any]:
    result = run_agent_prompt(
        AgentPromptRequest(
            prompt=prompt,
            prog_name="agent",
        )
    )
    result.pop("audit", None)
    return result
