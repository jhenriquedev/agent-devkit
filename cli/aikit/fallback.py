"""Controlled fallback helpers for agent runtime execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.aikit.credentials import CredentialResolverError
from cli.aikit.providers import ProviderRegistryError, load_providers, provider_status_with_credentials


READY_PROVIDER_STATUSES = {"ok", "unknown"}
FALLBACKS = {
    "plan_only",
    "dry_run",
    "manual_steps",
    "use_user_supplied_context",
    "skip_provider",
    "blocked",
}


def evaluate_provider_requirements(root: Path, capability: dict[str, Any], args: list[str] | None = None) -> dict[str, Any]:
    """Evaluate `requires.providers` without returning credential values."""
    requirements = provider_requirements(capability)
    if not requirements and not has_fixture_arg(args or []):
        requirements = infer_provider_requirements(root, capability)
    providers = {
        "used": [],
        "missing": [],
        "skipped": [],
        "details": [],
    }
    if not requirements:
        return ready_result(providers)

    for requirement in requirements:
        provider_id = str(requirement.get("id") or "").strip()
        if not provider_id:
            continue

        try:
            status_payload = provider_status_with_credentials(root, provider_id)
            status_item = status_payload["items"][0] if status_payload.get("items") else {}
        except (CredentialResolverError, ProviderRegistryError) as exc:
            status_item = {
                "id": provider_id,
                "status": "missing",
                "configured": False,
                "message": str(exc),
            }
        provider_status = str(status_item.get("status") or "missing")
        detail = provider_detail(requirement, status_item)
        providers["details"].append(detail)

        if provider_status in READY_PROVIDER_STATUSES:
            providers["used"].append(provider_id)
            continue

        providers["missing"].append(provider_id)
        fallback = normalize_fallback(requirement.get("fallback"))
        if fallback == "skip_provider":
            providers["skipped"].append(provider_id)
            continue

        providers["skipped"].append(provider_id)
        return fallback_result(provider_id, requirement, providers, fallback)

    return ready_result(providers)


def provider_requirements(capability: dict[str, Any]) -> list[dict[str, Any]]:
    requires = capability.get("requires", {}) or {}
    if not isinstance(requires, dict):
        return []
    providers = requires.get("providers", []) or []
    return [item for item in providers if isinstance(item, dict)]


def infer_provider_requirements(root: Path, capability: dict[str, Any]) -> list[dict[str, Any]]:
    capability_id = str(capability.get("id") or "")
    if "." not in capability_id:
        return []
    agent_id, short_capability = capability_id.rsplit(".", 1)
    candidates = {f"{agent_id}/{short_capability}", capability_id}
    requirements: list[dict[str, Any]] = []
    try:
        providers = load_providers(root)
    except ProviderRegistryError:
        return []
    for provider in providers:
        capabilities = provider.get("capabilities") if isinstance(provider.get("capabilities"), dict) else {}
        matched_mode = None
        for mode in ("read", "write"):
            declared = capabilities.get(mode) if isinstance(capabilities, dict) else []
            if any(str(item) in candidates for item in (declared or [])):
                matched_mode = mode
                break
        if not matched_mode:
            continue
        fallbacks = list(provider.get("fallbacks", []) or [])
        requirements.append(
            {
                "id": provider.get("id"),
                "mode": "required",
                "fallback": fallbacks[0] if fallbacks else "blocked",
                "purpose": f"inferred from provider registry for {agent_id}/{short_capability}",
                "access": matched_mode,
                "inferred": True,
            }
        )
    return requirements


def has_fixture_arg(args: list[str]) -> bool:
    for index, item in enumerate(args):
        if item == "--fixture" and index + 1 < len(args):
            return True
        if item.startswith("--fixture="):
            return True
    return False


def provider_detail(requirement: dict[str, Any], status_item: dict[str, Any]) -> dict[str, Any]:
    provider_id = str(requirement.get("id") or "")
    return {
        "id": provider_id,
        "mode": requirement.get("mode") or "required",
        "fallback": normalize_fallback(requirement.get("fallback")),
        "status": status_item.get("status") or "missing",
        "configured": bool(status_item.get("configured")),
        "purpose": requirement.get("purpose"),
    }


def normalize_fallback(value: Any) -> str:
    fallback = str(value or "blocked")
    return fallback if fallback in FALLBACKS else "blocked"


def ready_result(providers: dict[str, Any]) -> dict[str, Any]:
    return {
        "ready": True,
        "status": "ok",
        "providers": providers,
        "fallback_applied": None,
        "evidence": [],
        "risks": [],
        "next_steps": [],
        "artifacts": [],
    }


def fallback_result(
    provider_id: str,
    requirement: dict[str, Any],
    providers: dict[str, Any],
    fallback: str,
) -> dict[str, Any]:
    blocked = fallback == "blocked"
    return {
        "ready": False,
        "status": "blocked" if blocked else "partial",
        "providers": providers,
        "fallback_applied": fallback,
        "evidence": [],
        "risks": fallback_risks(provider_id, requirement, fallback),
        "next_steps": fallback_next_steps(provider_id, fallback),
        "artifacts": [],
        "exit_code": 2 if blocked else 0,
    }


def fallback_risks(provider_id: str, requirement: dict[str, Any], fallback: str) -> list[str]:
    risks = []
    if provider_id == "elasticsearch":
        risks.append("Logs reais nao foram consultados.")
    else:
        risks.append(f"Dados reais do provider {provider_id} nao foram consultados.")

    if fallback == "dry_run":
        risks.append("Nenhuma mutacao real foi executada.")
    if requirement.get("mode") == "required":
        risks.append("A capability declarou este provider como obrigatorio.")
    return risks


def fallback_next_steps(provider_id: str, fallback: str) -> list[str]:
    steps = [
        f"Configurar o provider com `agent provider configure {provider_id}`.",
    ]
    if fallback == "plan_only":
        steps.append("Usar o plano/checklist gerado como preparacao para a execucao real.")
    elif fallback == "dry_run":
        steps.append("Reexecutar sem fallback depois de validar credenciais e escopo de escrita.")
    elif fallback == "manual_steps":
        steps.append("Executar manualmente os passos indicados no sistema de origem.")
    elif fallback == "use_user_supplied_context":
        steps.append("Fornecer evidencias coladas no prompt ou em arquivos locais.")
    elif fallback == "blocked":
        steps.append("Sem fallback seguro declarado; configure o provider antes de executar.")
    return steps
