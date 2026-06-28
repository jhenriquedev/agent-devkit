"""Local Agent DevKit personality persistence."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cli.aikit.identity import DEFAULT_PUBLIC_NAME
from cli.aikit.memory import MEMORY_FILE_TEMPLATES, ensure_memory, memory_home


FIELD_LABELS = {
    "agent_name": "Name",
    "user_name": "User name",
    "language": "Language",
    "tone": "Tone",
    "detail_level": "Detail level",
}


def personality_path() -> Path:
    ensure_memory()
    return memory_home() / "personality.md"


def load_personality() -> dict[str, Any]:
    path = personality_path()
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return {
        "kind": "personality",
        "status": "ok",
        "path": str(path),
        "agent_name": parse_field(text, FIELD_LABELS["agent_name"]) or DEFAULT_PUBLIC_NAME,
        "user_name": parse_field(text, FIELD_LABELS["user_name"]),
        "language": parse_field(text, FIELD_LABELS["language"]),
        "tone": parse_field(text, FIELD_LABELS["tone"]) or "direct",
        "detail_level": parse_field(text, FIELD_LABELS["detail_level"]) or "concise",
        "questions": setup_questions(),
    }


def update_personality(
    *,
    agent_name: str | None = None,
    user_name: str | None = None,
    language: str | None = None,
    tone: str | None = None,
    detail_level: str | None = None,
) -> dict[str, Any]:
    current = load_personality()
    values = {
        "agent_name": clean_field(agent_name) or current.get("agent_name") or DEFAULT_PUBLIC_NAME,
        "user_name": clean_field(user_name) if user_name is not None else current.get("user_name"),
        "language": clean_field(language) if language is not None else current.get("language"),
        "tone": clean_field(tone) or current.get("tone") or "direct",
        "detail_level": clean_field(detail_level) or current.get("detail_level") or "concise",
    }
    path = personality_path()
    path.write_text(render_personality(values), encoding="utf-8")
    payload = load_personality()
    payload["status"] = "updated"
    return payload


def reset_personality() -> dict[str, Any]:
    path = personality_path()
    path.write_text(MEMORY_FILE_TEMPLATES["personality.md"], encoding="utf-8")
    payload = load_personality()
    payload["status"] = "reset"
    return payload


def setup_personality() -> dict[str, Any]:
    payload = load_personality()
    payload["status"] = "needs-input"
    payload["message"] = "Use `agent personality edit --name <nome>` to configure personality non-interactively."
    return payload


def render_personality(values: dict[str, Any]) -> str:
    return f"""# Personality

Configured public identity and response style for Agent DevKit.

## Agent

- Name: {values.get("agent_name") or DEFAULT_PUBLIC_NAME}
- User name: {values.get("user_name") or ""}
- Language: {values.get("language") or ""}

## Style

- Tone: {values.get("tone") or "direct"}
- Detail level: {values.get("detail_level") or "concise"}
"""


def parse_field(text: str, label: str) -> str | None:
    pattern = re.compile(rf"(?im)^[ \t]*-[ \t]*{re.escape(label)}[ \t]*:[ \t]*([^\r\n]*)[ \t]*$")
    match = pattern.search(text)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def clean_field(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).split())
    return cleaned or None


def setup_questions() -> list[str]:
    return [
        "Como voce deseja que eu me chame?",
        "Deseja criar um comando com esse nome para me chamar diretamente?",
        "Como voce se chama?",
        "Em qual idioma devo responder por padrao?",
        "Voce prefere respostas curtas, detalhadas, criticas ou didaticas?",
        "Qual backend LLM voce prefere como primario?",
    ]
