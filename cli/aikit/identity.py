"""Agent DevKit public identity helpers."""

from __future__ import annotations

import re
from typing import Any


BACKEND_IDENTITY_PATTERN = re.compile(
    r"(?i)\b("
    r"sou\s+(?:o\s+|a\s+)?(?:claude|codex|chatgpt)|"
    r"meu\s+nome\s+(?:e|é)\s+(?:claude|codex|chatgpt)|"
    r"i\s*am\s+(?:claude|codex|chatgpt)|"
    r"i'm\s+(?:claude|codex|chatgpt)|"
    r"my\s+name\s+is\s+(?:claude|codex|chatgpt)|"
    r"(?:da|from)\s+(?:anthropic|openai)"
    r")\b"
)

IDENTITY_QUESTION_PATTERN = re.compile(
    r"(?i)\b("
    r"qual\s+(?:e|é)\s+(?:o\s+)?seu\s+nome|"
    r"quem\s+(?:e|é)\s+voce|"
    r"quem\s+(?:e|é)\s+você|"
    r"voce\s+esta\s+vivo|"
    r"você\s+est[aá]\s+vivo|"
    r"vc\s+est[aá]\s+vivo|"
    r"seu\s+nome"
    r")\b"
)

DEFAULT_PUBLIC_NAME = "Agent DevKit"
CANONICAL_PROGRAM_NAMES = {"agent", "aikit", "ai-devkit"}


def display_name(value: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[-_\s]+", value) if part) or DEFAULT_PUBLIC_NAME


def public_name(*, personality: dict[str, Any] | None = None, invoked_as: str | None = None) -> str:
    invoked = (invoked_as or "").strip()
    if invoked and invoked not in CANONICAL_PROGRAM_NAMES:
        return display_name(invoked)
    configured = str((personality or {}).get("agent_name") or "").strip()
    return configured or DEFAULT_PUBLIC_NAME


def is_identity_question(prompt: str) -> bool:
    return bool(IDENTITY_QUESTION_PATTERN.search(prompt))


def local_identity_response(prompt: str, *, name: str) -> str:
    if re.search(r"(?i)vivo|viva", prompt):
        return f"Estou disponivel. Meu nome e {name}, seu agente local do Agent DevKit."
    return f"Meu nome e {name}."


def identity_system_prompt(*, name: str) -> str:
    return (
        f"Voce e {name}, o agente local do Agent DevKit. "
        "A LLM conectada e apenas o motor de raciocinio, nao sua identidade publica. "
        "Nunca responda que voce e Claude, Codex, ChatGPT, OpenAI ou Anthropic. "
        "Se perguntarem seu nome, responda usando apenas a identidade publica configurada. "
        "Seja direto, operacional e nao peca todas as credenciais de uma vez."
    )


def host_cli_prompt(prompt: str, *, name: str) -> str:
    return f"{identity_system_prompt(name=name)}\n\nPedido do usuario:\n{prompt}"


def enforce_identity_response(response: str, prompt: str, *, name: str) -> str:
    if BACKEND_IDENTITY_PATTERN.search(response):
        return local_identity_response(prompt, name=name)
    return response
