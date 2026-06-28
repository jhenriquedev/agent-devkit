"""Natural-language control routing for tools, integrations, skills and LLMs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cli.aikit.decision_store import forget_decision, list_decisions, reset_decisions, set_decision
from cli.aikit.llm import BACKENDS
from cli.aikit.providers import load_providers
from cli.aikit.toolchain import load_toolchain


CATEGORY_ALIASES: dict[str, tuple[str, ...]] = {
    "tools": ("tool", "tools", "ferramenta", "ferramentas", "cli", "clis", "toolchain"),
    "integrations": ("integration", "integrations", "integracao", "integracoes", "integração", "integrações", "provider", "providers"),
    "skills": ("skill", "skills", "habilidade", "habilidades"),
    "llms": ("llm", "llms", "modelo", "modelos", "backend", "backends"),
}
LIST_MARKERS = ("mostre", "mostrar", "liste", "listar", "ver", "exiba", "exibir")
ENABLE_MARKERS = ("reative", "ative", "habilite", "enable")
DISABLE_MARKERS = ("desative", "desabilite", "disable", "bloqueie", "bloquear")
FORGET_MARKERS = ("esqueca", "esqueça", "remova", "remover", "limpe", "limpar", "delete", "apague", "apagar")
DECISION_MARKERS = ("decisao", "decisão", "decisoes", "decisões", "decision", "decisions", "bloqueio")
TOKEN_PATTERN = re.compile(r"[a-z0-9._:-]+")
SKILL_ROW_PATTERN = re.compile(r"^\|\s*`([^`]+)`\s*\|")


def dispatch_natural_control_prompt(root: Path, normalized_prompt: str) -> dict[str, Any] | None:
    action = detect_action(normalized_prompt)
    category = detect_category(normalized_prompt)
    if action == "list":
        return list_payload(root, category=category)
    if action == "reset" and category:
        result = reset_decisions(category)
        return control_payload(
            status="ok",
            response=f"Decisoes de {category} foram resetadas.",
            result={"action": "reset", "category": category, "decision": result},
        )
    if action not in {"enable", "disable", "forget"}:
        return None

    index = build_control_index(root)
    matches = resolve_target(index, normalized_prompt, category=category)
    if not matches:
        return needs_input_unknown(root, normalized_prompt, category=category)
    if len(matches) > 1:
        return needs_input_ambiguous(matches, normalized_prompt, category=category)

    target = matches[0]
    if action == "forget":
        decision = forget_decision(str(target["category"]), str(target["id"]))
        return control_payload(
            status="ok",
            response=f"Decisao local sobre {target['id']} removida.",
            result={"action": "forget", "category": target["category"], "id": target["id"], "removed": decision.get("removed"), "decision": decision},
        )

    state = "enabled" if action == "enable" else "disabled_by_user"
    decision = set_decision(str(target["category"]), str(target["id"]), state, reason=f"natural prompt: {action}")
    return control_payload(
        status="ok",
        response=f"{target['id']} foi {'ativado' if state == 'enabled' else 'desativado'} para {target['category']}.",
        result={"action": action, "category": target["category"], "id": target["id"], "state": state, "decision": decision.get("item")},
    )


def plan_natural_control_prompt(root: Path, normalized_prompt: str) -> dict[str, Any] | None:
    action = detect_action(normalized_prompt)
    category = detect_category(normalized_prompt)
    if action == "list":
        payload = list_payload(root, category=category)
        payload["dry_run"] = True
        return payload
    if action == "reset" and category:
        return control_payload(
            status="planned",
            response=f"Dry-run: decisoes de {category} seriam resetadas.",
            result={"action": "reset", "category": category},
        ) | {"dry_run": True, "ok": True}
    if action not in {"enable", "disable", "forget"}:
        return None
    index = build_control_index(root)
    matches = resolve_target(index, normalized_prompt, category=category)
    if not matches:
        payload = needs_input_unknown(root, normalized_prompt, category=category)
        payload["dry_run"] = True
        return payload
    if len(matches) > 1:
        payload = needs_input_ambiguous(matches, normalized_prompt, category=category)
        payload["dry_run"] = True
        return payload
    target = matches[0]
    state = "enabled" if action == "enable" else "disabled_by_user"
    return control_payload(
        status="planned",
        response=f"Dry-run: {target['id']} seria {'ativado' if action == 'enable' else 'desativado' if action == 'disable' else 'removido das decisoes'} para {target['category']}.",
        result={"action": action, "category": target["category"], "id": target["id"], "state": state if action != "forget" else None},
    ) | {"dry_run": True, "ok": True}


def build_control_index(root: Path) -> dict[str, list[dict[str, Any]]]:
    return {
        "tools": tool_items(root),
        "integrations": integration_items(root),
        "skills": skill_items(root),
        "llms": llm_items(),
    }


def tool_items(root: Path) -> list[dict[str, Any]]:
    return [
        item("tools", tool_id, label=str(spec.get("label") or tool_id), source="toolchain", aliases=aliases_for(tool_id, spec.get("label")))
        for tool_id, spec in load_toolchain(root).items()
    ]


def integration_items(root: Path) -> list[dict[str, Any]]:
    items = []
    for provider in load_providers(root):
        provider_id = str(provider.get("id") or "")
        if provider_id:
            items.append(item("integrations", provider_id, label=str(provider.get("name") or provider_id), source="providers", aliases=aliases_for(provider_id, provider.get("name"))))
    return items


def skill_items(root: Path) -> list[dict[str, Any]]:
    catalog = root / "vendor" / "skills" / "CATALOG.md"
    if not catalog.exists():
        return []
    items = []
    for line in catalog.read_text(encoding="utf-8").splitlines():
        match = SKILL_ROW_PATTERN.match(line)
        if not match:
            continue
        skill_id = match.group(1).strip()
        if skill_id and skill_id.lower() != "skill":
            items.append(item("skills", skill_id, label=skill_id, source="vendor-skills", aliases=aliases_for(skill_id)))
    return items


def llm_items() -> list[dict[str, Any]]:
    return [
        item("llms", backend_id, label=backend.display_name, source="llm-backends", aliases=aliases_for(backend_id, backend.display_name))
        for backend_id, backend in BACKENDS.items()
    ]


def item(category: str, item_id: str, *, label: str, source: str, aliases: set[str]) -> dict[str, Any]:
    return {"category": category, "id": item_id, "label": label, "source": source, "aliases": sorted(aliases)}


def aliases_for(item_id: str, label: Any = None) -> set[str]:
    values = {normalize(item_id)}
    if label:
        values.add(normalize(str(label)))
    values.add(normalize(item_id.replace("-", " ")))
    values.add(normalize(item_id.replace("_", " ")))
    for token in re.split(r"[-_\s]+", item_id):
        normalized = normalize(token)
        if normalized and normalized not in {"cli", "mcp", "api", "tool", "skill", "plugin"}:
            values.add(normalized)
    if item_id.endswith("-cli"):
        values.add(normalize(item_id.removesuffix("-cli")))
    if item_id.endswith("-mcp"):
        values.add(normalize(item_id.removesuffix("-mcp")))
    return {value for value in values if value}


def detect_action(prompt: str) -> str | None:
    if contains_any(prompt, LIST_MARKERS):
        return "list"
    if contains_any(prompt, FORGET_MARKERS) and contains_any(prompt, DECISION_MARKERS) and detect_category(prompt):
        return "reset"
    if contains_any(prompt, FORGET_MARKERS) and contains_any(prompt, DECISION_MARKERS):
        return "forget"
    if contains_any(prompt, FORGET_MARKERS) and detect_category(prompt):
        return "reset"
    if contains_any(prompt, DISABLE_MARKERS):
        return "disable"
    if contains_any(prompt, ENABLE_MARKERS):
        return "enable"
    return None


def detect_category(prompt: str) -> str | None:
    for category, aliases in CATEGORY_ALIASES.items():
        if contains_any(prompt, aliases):
            return category
    return None


def list_payload(root: Path, *, category: str | None) -> dict[str, Any]:
    index = build_control_index(root)
    if category:
        result = {
            "kind": "control-index",
            "status": "ok",
            "category": category,
            "items": public_items(index.get(category, [])),
            "decisions": list_decisions(category),
        }
        return control_payload(status="ok", response=f"Estes sao os itens catalogados para {category}.", result=result)
    result = {
        "kind": "control-index",
        "status": "ok",
        "categories": {key: public_items(value) for key, value in index.items()},
        "decisions": list_decisions(),
    }
    return control_payload(status="ok", response="Estes sao os recursos controlaveis catalogados.", result=result)


def resolve_target(index: dict[str, list[dict[str, Any]]], prompt: str, *, category: str | None) -> list[dict[str, Any]]:
    candidates = index.get(category, []) if category else [item for items in index.values() for item in items]
    prompt_tokens = set(TOKEN_PATTERN.findall(prompt))
    matches = []
    for candidate in candidates:
        aliases = set(candidate.get("aliases") or [])
        if any(alias_matches_prompt(alias, prompt, prompt_tokens) for alias in aliases):
            matches.append(candidate)
            continue
        candidate_tokens = set(TOKEN_PATTERN.findall(normalize(str(candidate.get("id") or ""))))
        if candidate_tokens and candidate_tokens <= prompt_tokens:
            matches.append(candidate)
    return sorted(unique_matches(matches), key=lambda item: (str(item["category"]), str(item["id"])))


def unique_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    unique = []
    for match in matches:
        key = (str(match.get("category")), str(match.get("id")))
        if key not in seen:
            seen.add(key)
            unique.append(match)
    return unique


def alias_matches_prompt(alias: str, prompt: str, prompt_tokens: set[str]) -> bool:
    if not alias:
        return False
    alias_tokens = set(TOKEN_PATTERN.findall(alias))
    if len(alias_tokens) == 1:
        return alias in prompt_tokens
    return alias in prompt


def needs_input_unknown(root: Path, prompt: str, *, category: str | None) -> dict[str, Any]:
    index = build_control_index(root)
    categories = [category] if category else sorted(index)
    return {
        "kind": "agent",
        "status": "needs-input",
        "ok": False,
        "mode": "control-center-route",
        "requires_llm": False,
        "unknown_control_target": True,
        "category": category,
        "prompt": prompt,
        "available_categories": categories,
        "response": "Nao encontrei esse recurso nos catalogos locais controlaveis.",
        "result": {"categories": {key: public_items(index.get(key, [])) for key in categories}},
        "exit_code": 2,
    }


def needs_input_ambiguous(matches: list[dict[str, Any]], prompt: str, *, category: str | None) -> dict[str, Any]:
    return {
        "kind": "agent",
        "status": "needs-input",
        "ok": False,
        "mode": "control-center-route",
        "requires_llm": False,
        "ambiguous_control_target": True,
        "category": category,
        "prompt": prompt,
        "matches": public_items(matches),
        "response": "Encontrei mais de um recurso compativel. Informe a categoria ou id exato.",
        "exit_code": 2,
    }


def control_payload(*, status: str, response: str, result: dict[str, Any]) -> dict[str, Any]:
    return {"kind": "agent", "status": status, "ok": status == "ok", "mode": "control-center-route", "requires_llm": False, "response": response, "result": result}


def public_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"category": item.get("category"), "id": item.get("id"), "label": item.get("label"), "source": item.get("source")} for item in items]


def contains_any(prompt: str, markers: tuple[str, ...]) -> bool:
    return any(normalize(marker) in prompt for marker in markers)


def normalize(value: str) -> str:
    return " ".join(value.lower().split())
