"""Global configuration orchestration for missing providers and sources."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cli.aikit.decision_store import is_disabled
from cli.aikit.providers import ProviderRegistryError, load_providers, provider_or_error


PROJECT_PATTERN = re.compile(r"(?i)\bprojeto\s+([A-Za-z0-9._ -]{2,80}?)(?:\s+no\b|\s+na\b|\s+do\b|\s+da\b|$)")


def provider_setup_wizard(
    root: Path,
    provider_id: str,
    *,
    prompt: str | None = None,
    route: dict[str, Any] | None = None,
    agent_id: str | None = None,
    capability_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    provider = load_provider(root, provider_id)
    provider_name = str(provider.get("name") or provider_id)
    intent = str((route or {}).get("intent") or capability_id or "provider-configuration")
    suggested_project = infer_project(prompt or "")
    source_context = bool(route and route.get("intent"))
    suggested_source_id = suggest_source_id(provider_id, suggested_project)
    disabled = is_disabled("tools", provider_id) or is_disabled("integrations", provider_id)
    questions = build_questions(provider, suggested_project=suggested_project, suggested_source_id=suggested_source_id, include_source=source_context)
    next_question = disabled_notice(provider_id, provider_name) if disabled else opt_in_question(provider_id, provider_name)
    return {
        "kind": "provider-setup-wizard",
        "status": "denied-by-user" if disabled else "waiting-for-user",
        "provider": provider_id,
        "provider_name": provider_name,
        "provider_kind": provider.get("kind"),
        "intent": intent,
        "agent_id": agent_id or (route or {}).get("agent_id"),
        "capability_id": capability_id or (route or {}).get("capability_id"),
        "reason": reason,
        "resume_prompt": prompt,
        "suggested_source_id": suggested_source_id if source_context else None,
        "suggested_config": suggested_config(provider_id, suggested_project),
        "next_question": next_question,
        "questions": questions,
        "credential_options": credential_options(provider),
        "config_fields": public_config_fields(provider),
        "auth_methods": public_auth_methods(provider),
        "fallbacks": list(provider.get("fallbacks", []) or []),
        "stores_secret": False,
        "owner_agent": "provider-configurator",
        "message": (
            f"{provider_name} esta desativado. O agente seguira sem essa ferramenta ate voce reativar."
            if disabled
            else f"Para continuar, o agente precisa configurar ou autorizar {provider_name}."
        ),
    }


def provider_wizard_from_requirement(
    root: Path,
    provider_id: str,
    *,
    agent_id: str | None = None,
    capability_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    return provider_setup_wizard(
        root,
        provider_id,
        agent_id=agent_id,
        capability_id=capability_id,
        reason=reason or "Capability provider requirement is not configured.",
    )


def load_provider(root: Path, provider_id: str) -> dict[str, Any]:
    try:
        return provider_or_error(load_providers(root), provider_id)
    except ProviderRegistryError:
        return {
            "id": provider_id,
            "name": provider_id,
            "kind": "unknown",
            "config_fields": [],
            "auth_methods": [],
            "fallbacks": [],
        }


def build_questions(
    provider: dict[str, Any],
    *,
    suggested_project: str | None,
    suggested_source_id: str,
    include_source: bool,
) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for field in provider.get("config_fields", []) or []:
        if not isinstance(field, dict):
            continue
        name = str(field.get("name") or "").strip()
        if not name:
            continue
        suggested_value = suggested_value_for_field(provider, name, suggested_project)
        questions.append(
            {
                "id": field_question_id(provider["id"], name),
                "type": "text",
                "text": question_text(provider, name, suggested_value=suggested_value),
                "config_key": name,
                "env": name,
                "required": bool(field.get("required")),
                "secret": bool(field.get("secret")),
                "default": field.get("default"),
                "suggested_value": suggested_value,
            }
        )
    auth_methods = public_auth_methods(provider)
    if auth_methods:
        questions.append(
            {
                "id": f"{provider_slug(str(provider['id']))}_auth",
                "type": "select",
                "text": "Como deseja autenticar?",
                "options": [method["id"] for method in auth_methods] + ["env", "file", "skip"],
                "auth_methods": auth_methods,
            }
        )
    if include_source:
        questions.append(
            {
                "id": "source_id",
                "type": "text",
                "text": "Qual nome local deseja dar para esta fonte?",
                "suggested_value": suggested_source_id,
            }
        )
        questions.append(
            {
                "id": "default_for_intent",
                "type": "confirm",
                "text": "Posso usar esta fonte como padrao para este tipo de pedido?",
                "default": True,
            }
        )
    if not questions:
        questions.append(
            {
                "id": f"{provider_slug(str(provider['id']))}_confirm",
                "type": "confirm",
                "text": f"Posso tentar usar {provider.get('name') or provider['id']} com a cadeia de credenciais nativa?",
                "default": False,
            }
        )
    return questions


def opt_in_question(provider_id: str, provider_name: str) -> dict[str, Any]:
    return {
        "id": f"{provider_slug(provider_id)}_opt_in",
        "type": "confirm",
        "text": f"Posso configurar ou autorizar {provider_name} para atender este pedido?",
        "default": False,
    }


def disabled_notice(provider_id: str, provider_name: str) -> dict[str, Any]:
    return {
        "id": f"{provider_slug(provider_id)}_disabled",
        "type": "notice",
        "text": f"{provider_name} esta desativado por decisao do usuario. Reative para usar esta integracao.",
        "default": False,
    }


def public_config_fields(provider: dict[str, Any]) -> list[dict[str, Any]]:
    fields = []
    for field in provider.get("config_fields", []) or []:
        if not isinstance(field, dict):
            continue
        fields.append(
            {
                "name": field.get("name"),
                "required": bool(field.get("required")),
                "secret": bool(field.get("secret")),
                "default": field.get("default"),
            }
        )
    return fields


def public_auth_methods(provider: dict[str, Any]) -> list[dict[str, Any]]:
    methods = []
    for method in provider.get("auth_methods", []) or []:
        if not isinstance(method, dict):
            continue
        methods.append(
            {
                "id": method.get("id"),
                "label": method.get("label") or method.get("id"),
                "native": bool(method.get("native")),
                "config_fields": list(method.get("config_fields", []) or []),
                "secret_fields": list(method.get("secret_fields", []) or []),
            }
        )
    return methods


def credential_options(provider: dict[str, Any]) -> list[dict[str, Any]]:
    options = []
    for method in public_auth_methods(provider):
        for secret_field in method.get("secret_fields") or []:
            options.append(
                {
                    "id": f"env:{secret_field}",
                    "label": f"Variavel de ambiente {secret_field}",
                    "env": secret_field,
                    "auth_method": method.get("id"),
                    "stores_secret": False,
                }
            )
    options.extend(
        [
            {"id": "file", "label": "Arquivo local de credencial", "stores_secret": False},
            {"id": "native", "label": "Cadeia nativa ou CLI ja autenticada", "stores_secret": False},
            {"id": "skip", "label": "Ignorar esta ferramenta", "stores_secret": False},
        ]
    )
    seen: set[str] = set()
    unique = []
    for option in options:
        option_id = str(option.get("id"))
        if option_id not in seen:
            seen.add(option_id)
            unique.append(option)
    return unique


def suggested_config(provider_id: str, suggested_project: str | None) -> dict[str, Any]:
    config: dict[str, Any] = {}
    if provider_id == "azure-devops" and suggested_project:
        config["project"] = suggested_project
        config["AZURE_DEVOPS_PROJECT"] = suggested_project
    return config


def suggested_value_for_field(provider: dict[str, Any], name: str, suggested_project: str | None) -> str | None:
    if provider.get("id") == "azure-devops" and name == "AZURE_DEVOPS_PROJECT" and suggested_project:
        return suggested_project
    return None


def question_text(provider: dict[str, Any], name: str, *, suggested_value: str | None) -> str:
    if provider.get("id") == "azure-devops" and name == "AZURE_DEVOPS_ORG":
        return "Qual e a organizacao do Azure DevOps?"
    if provider.get("id") == "azure-devops" and name == "AZURE_DEVOPS_PROJECT":
        if suggested_value:
            return f'O projeto e "{suggested_value}"? Se nao, informe o nome correto.'
        return "Qual e o nome do projeto no Azure DevOps?"
    label = name.replace("_", " ").lower()
    return f"Informe {label} para {provider.get('name') or provider.get('id')}."


def field_question_id(provider_id: str, name: str) -> str:
    return f"{provider_slug(provider_id)}_{provider_slug(name)}"


def infer_project(prompt: str) -> str | None:
    match = PROJECT_PATTERN.search(prompt)
    if not match:
        return None
    project = " ".join(match.group(1).strip(" .,_-").split())
    return project or None


def suggest_source_id(provider: str, project: str | None) -> str:
    parts = [provider]
    if project:
        parts.append(project)
    raw = "-".join(parts)
    normalized = re.sub(r"[^a-z0-9._-]+", "-", raw.lower()).strip("-")
    return normalized or provider_slug(provider)


def provider_slug(provider: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", provider.lower()).strip("_") or "provider"
