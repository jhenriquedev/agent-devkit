"""Interactive setup wizard flow for CLI TTY sessions."""

from __future__ import annotations

import os
import sys
from typing import Any

from cli.aikit.core.requests import AgentPromptRequest
from cli.aikit.core.runtime import run_agent_prompt
from cli.aikit.aliases import setup_alias_path
from cli.aikit.llm import BACKENDS, configure_backend
from cli.aikit.mini_brain import DEFAULT_OLLAMA_MODEL
from cli.aikit.ollama import ollama_status
from cli.aikit.onboarding import onboarding_status
from cli.aikit.personality import load_personality, update_personality
from cli.aikit.runtime_paths import ROOT
from cli.aikit.wizard_state import WizardStateError, answer_wizard, cancel_wizard, show_wizard

ONBOARDING_MODE_OPTIONS = [
    {
        "id": "minimal",
        "number": "1",
        "label": "minimo",
        "description": "identidade, mini-cerebro local embarcado e memoria",
        "recommended": True,
    },
    {
        "id": "complete",
        "number": "2",
        "label": "completo",
        "description": "minimo + toolchain, sources, notificacoes, knowledge e memorias",
        "recommended": False,
    },
    {
        "id": "skip",
        "number": "3",
        "label": "pular",
        "description": "",
        "recommended": False,
    },
]


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
        print("O mini cerebro embarcado ja funciona; instale Ollama apenas se quiser workers locais adicionais.")
    elif ask_yes_no(f"Deseja instalar o modelo Ollama opcional {DEFAULT_OLLAMA_MODEL} para workers locais?", default=False):
        print("Rode: agent local-llm install " + DEFAULT_OLLAMA_MODEL + " --yes")

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
    selected = choose_onboarding_mode_with_arrows()
    if selected:
        return selected
    print("\nModos de onboarding:")
    for option in ONBOARDING_MODE_OPTIONS:
        print(format_onboarding_option(option, selected=False, include_selector=False))
    answer = ask_text("Escolha o modo:").strip().lower()
    return parse_onboarding_mode_answer(answer)


def choose_onboarding_mode_with_arrows() -> str | None:
    if not sys.stdin.isatty() or not sys.stdout.isatty() or os.environ.get("TERM") == "dumb":
        return None
    try:
        return read_onboarding_mode_selection()
    except KeyboardInterrupt:
        print()
        return "skip"
    except (OSError, ValueError):
        return None


def read_onboarding_mode_selection() -> str:
    selected_index = 0
    typed_answer = ""
    print("\nModos de onboarding:")
    render_onboarding_options(selected_index)
    print_onboarding_prompt(typed_answer)
    while True:
        key = read_key()
        if key in {"\x03", "\x04"}:
            raise KeyboardInterrupt
        if key in {"\r", "\n"}:
            if typed_answer:
                parsed = parse_onboarding_mode_answer(typed_answer.strip().lower(), default="")
                if parsed:
                    return parsed
                typed_answer = ""
                rerender_onboarding_options(selected_index, typed_answer)
                continue
            return str(ONBOARDING_MODE_OPTIONS[selected_index]["id"])
        if key in {"\x1b[A", "k"}:
            typed_answer = ""
            selected_index = (selected_index - 1) % len(ONBOARDING_MODE_OPTIONS)
            rerender_onboarding_options(selected_index, typed_answer)
            continue
        if key in {"\x1b[B", "j"}:
            typed_answer = ""
            selected_index = (selected_index + 1) % len(ONBOARDING_MODE_OPTIONS)
            rerender_onboarding_options(selected_index, typed_answer)
            continue
        if key in {"\x7f", "\b"}:
            typed_answer = typed_answer[:-1]
            rerender_onboarding_options(selected_index, typed_answer)
            continue
        parsed = parse_onboarding_mode_answer(key.strip().lower(), default="")
        if parsed:
            print()
            return parsed
        if key.isprintable():
            typed_answer += key
            rerender_onboarding_options(selected_index, typed_answer)


def render_onboarding_options(selected_index: int) -> None:
    for index, option in enumerate(ONBOARDING_MODE_OPTIONS):
        print(format_onboarding_option(option, selected=index == selected_index, include_selector=True))


def rerender_onboarding_options(selected_index: int, typed_answer: str) -> None:
    lines_to_move = len(ONBOARDING_MODE_OPTIONS) + 1
    sys.stdout.write(f"\x1b[{lines_to_move}A")
    for index, option in enumerate(ONBOARDING_MODE_OPTIONS):
        sys.stdout.write("\x1b[2K")
        sys.stdout.write(format_onboarding_option(option, selected=index == selected_index, include_selector=True) + "\n")
    sys.stdout.write("\x1b[2K")
    sys.stdout.write(onboarding_prompt_line(typed_answer) + "\n")
    sys.stdout.flush()


def format_onboarding_option(option: dict[str, Any], *, selected: bool, include_selector: bool) -> str:
    selector = "> " if selected else "  "
    prefix = selector if include_selector else ""
    description = f": {option['description']}" if option.get("description") else ""
    recommended = " (Recomendado)" if option.get("recommended") else ""
    return f"{prefix}{option['number']}. {option['label']}{description}{recommended}"


def parse_onboarding_mode_answer(answer: str, *, default: str = "minimal") -> str:
    if not answer:
        return default
    if answer in {"1", "minimo", "mínimo", "minimal"}:
        return "minimal"
    if answer in {"2", "completo", "complete", "full"}:
        return "complete"
    if answer in {"3", "pular", "skip", "cancelar", "cancel"}:
        return "skip"
    return default


def print_onboarding_prompt(typed_answer: str) -> None:
    print(onboarding_prompt_line(typed_answer))


def onboarding_prompt_line(typed_answer: str) -> str:
    suffix = f" {typed_answer}" if typed_answer else ""
    return f"Escolha o modo:{suffix}"


def read_key() -> str:
    if os.name == "nt":
        import msvcrt

        char = msvcrt.getwch()
        if char in {"\x00", "\xe0"}:
            code = msvcrt.getwch()
            if code == "H":
                return "\x1b[A"
            if code == "P":
                return "\x1b[B"
        return char

    import termios
    import tty
    import select

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
        if char == "\x1b":
            sequence = ""
            for _ in range(2):
                ready, _, _ = select.select([sys.stdin], [], [], 0.01)
                if not ready:
                    break
                sequence += sys.stdin.read(1)
            char += sequence
        return char
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def configure_personality_interactively(agent: dict[str, Any]) -> None:
    current_name = str(agent.get("name") or "Agent DevKit")
    current_tone = str(agent.get("tone") or "direct")
    current_detail = str(agent.get("detail_level") or "concise")
    agent_name = ask_text("Como devo me chamar?", default=current_name)
    user_name = ask_text("Como voce se chama?", default=str(agent.get("user_name") or ""))
    language = ask_text("Idioma padrao das respostas?", default=str(agent.get("language") or "pt-BR"))
    tone = ask_text("Tom das respostas?", default=current_tone)
    detail_level = ask_text("Nivel de detalhe?", default=current_detail)
    payload = update_personality(
        agent_name=agent_name,
        user_name=user_name,
        language=language,
        tone=tone,
        detail_level=detail_level,
    )
    alias = payload.get("alias") if isinstance(payload.get("alias"), dict) else None
    if not alias:
        return
    if alias.get("status") == "added":
        print(f"Comando local criado: {alias.get('name')}")
    elif alias.get("message"):
        print(f"Alias nao configurado automaticamente: {alias['message']}")
    path_status = alias.get("path_status") if isinstance(alias.get("path_status"), dict) else {}
    if path_status.get("setup_required"):
        bin_dir = path_status.get("bin_dir")
        print(f"O comando foi criado em {bin_dir}, mas essa pasta ainda nao esta no PATH.")
        if ask_yes_no("Deseja habilitar aliases do Agent DevKit no shell para proximas sessoes?", default=True):
            setup = setup_alias_path(yes=True)
            print(setup.get("message") or "PATH de aliases atualizado.")


def configure_llm_interactively() -> None:
    print("\nNenhum backend LLM coordenador externo utilizavel foi detectado.")
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
