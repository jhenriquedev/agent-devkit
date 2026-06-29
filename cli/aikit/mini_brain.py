"""Mini-brain local model contract and setup helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from cli.aikit.llm import BACKENDS, configure_backend, doctor_backend, load_config, save_config
from cli.aikit.ollama import ollama_pull, ollama_status


MINI_BRAIN_CONFIG_KEY = "mini_brain"
DEFAULT_HF_MODEL = "Qwen/Qwen3-0.6B"
DEFAULT_OLLAMA_MODEL = "qwen3:0.6b"
DEFAULT_PROVIDER = "ollama"
DEFAULT_BASE_URL = "http://localhost:11434/v1"
ALLOWED_TASKS = [
    "setup_help",
    "wizard_conversation",
    "intent_classification",
    "command_explanation",
    "short_error_summary",
]
FORBIDDEN_TASKS = [
    "external_write_decision",
    "destructive_operation_approval",
    "security_review_final",
    "architecture_decision",
    "secret_handling",
    "final_delivery_decision",
]
DEFAULT_LIMITS = {
    "max_context_chars": 6000,
    "max_response_chars": 2000,
    "max_llm_calls": 1,
}
DEFAULT_GUARDRAILS = [
    "no_secrets",
    "low_risk_only",
    "no_external_writes",
    "coordinator_review_required",
]


def mini_brain_contract(
    *,
    config: dict[str, Any] | None = None,
    ollama_payload: dict[str, Any] | None = None,
    ollama_backend: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = load_config() if config is None else config
    stored = config.get(MINI_BRAIN_CONFIG_KEY) if isinstance(config.get(MINI_BRAIN_CONFIG_KEY), dict) else {}
    enabled = bool(stored.get("enabled"))
    provider = stored.get("provider") or stored.get("runtime") or DEFAULT_PROVIDER
    hf_model = stored.get("hf_model") or stored.get("model") or DEFAULT_HF_MODEL
    ollama_model = stored.get("ollama_model") or DEFAULT_OLLAMA_MODEL
    ollama_payload = ollama_status() if ollama_payload is None else ollama_payload
    ollama_backend = doctor_backend(BACKENDS["ollama"], config) if ollama_backend is None else ollama_backend
    backend_configured = ollama_backend.get("status") == "ok"
    runtime_available = ollama_payload.get("status") == "ok" or backend_configured
    available = enabled and provider == DEFAULT_PROVIDER and runtime_available
    status = "ok" if available else "disabled" if not enabled else "unavailable"
    return {
        "kind": "mini-brain",
        "status": status,
        "enabled": enabled,
        "available": available,
        "configured": enabled and provider == DEFAULT_PROVIDER and backend_configured,
        "provider": provider,
        "runtime": provider,
        "hf_model": hf_model,
        "model": hf_model,
        "ollama_model": ollama_model,
        "allowed_tasks": list_value(stored.get("allowed_tasks"), ALLOWED_TASKS),
        "forbidden_tasks": list_value(stored.get("forbidden_tasks"), FORBIDDEN_TASKS),
        "limits": dict_value(stored.get("limits"), DEFAULT_LIMITS),
        "guardrails": list_value(stored.get("guardrails"), DEFAULT_GUARDRAILS),
        "stored_secret": False,
        "ollama": {
            "status": ollama_payload.get("status"),
            "daemon": (ollama_payload.get("daemon") or {}).get("status")
            if isinstance(ollama_payload.get("daemon"), dict)
            else None,
            "model_count": ollama_payload.get("model_count"),
        },
        "backend": {
            "status": ollama_backend.get("status"),
            "model": ollama_backend.get("model"),
            "base_url": ollama_backend.get("base_url"),
        },
    }


def setup_mini_brain(
    *,
    dry_run: bool = False,
    yes: bool = False,
    set_default: bool = False,
    model: str = DEFAULT_OLLAMA_MODEL,
) -> dict[str, Any]:
    if dry_run or not yes:
        status = "planned" if dry_run else "needs-confirmation"
        return {
            "kind": "mini-brain-setup",
            "status": status,
            "ok": bool(dry_run),
            "dry_run": dry_run,
            "yes": yes,
            "stored_secret": False,
            "mini_brain": planned_contract(model=model),
            "pull": ollama_pull(model, yes=False, dry_run=dry_run),
            "next_steps": ["agent setup mini-brain --yes"],
            "message": "Use --yes to pull Qwen3-0.6B with Ollama and enable the mini-brain.",
        }

    pull = ollama_pull(model, yes=True, dry_run=False)
    if not pull.get("ok"):
        return {
            "kind": "mini-brain-setup",
            "status": "failed",
            "ok": False,
            "dry_run": False,
            "yes": True,
            "stored_secret": False,
            "mini_brain": planned_contract(model=model),
            "pull": pull,
            "next_steps": ["Install Ollama or run agent ollama pull qwen3:0.6b --yes"],
            "message": pull.get("message") or "Could not pull the mini-brain model.",
        }

    existing_config = load_config()
    existing_ollama = (
        existing_config.get("llm", {}).get("backends", {}).get(DEFAULT_PROVIDER)
        if isinstance(existing_config.get("llm"), dict)
        else {}
    )
    existing_base_url = existing_ollama.get("base_url") if isinstance(existing_ollama, dict) else None
    configured = configure_backend(
        DEFAULT_PROVIDER,
        base_url=existing_base_url or DEFAULT_BASE_URL,
        model=model,
        set_default=set_default,
    )
    config = load_config()
    config[MINI_BRAIN_CONFIG_KEY] = stored_config(model=model)
    written_path = save_config(config)
    contract = mini_brain_contract(config=config)
    return {
        "kind": "mini-brain-setup",
        "status": "configured",
        "ok": True,
        "dry_run": False,
        "yes": True,
        "stored_secret": False,
        "config_path": str(written_path),
        "mini_brain": contract,
        "pull": pull,
        "llm_configure": configured,
        "next_steps": ["Use low-risk setup, wizard and summary prompts normally."],
    }


def planned_contract(*, model: str = DEFAULT_OLLAMA_MODEL) -> dict[str, Any]:
    return {
        "kind": "mini-brain",
        "status": "planned",
        "enabled": False,
        "available": False,
        "configured": False,
        "provider": DEFAULT_PROVIDER,
        "runtime": DEFAULT_PROVIDER,
        "hf_model": DEFAULT_HF_MODEL,
        "model": DEFAULT_HF_MODEL,
        "ollama_model": model,
        "allowed_tasks": list(ALLOWED_TASKS),
        "forbidden_tasks": list(FORBIDDEN_TASKS),
        "limits": dict(DEFAULT_LIMITS),
        "guardrails": list(DEFAULT_GUARDRAILS),
        "stored_secret": False,
    }


def stored_config(*, model: str = DEFAULT_OLLAMA_MODEL) -> dict[str, Any]:
    return {
        "enabled": True,
        "provider": DEFAULT_PROVIDER,
        "runtime": DEFAULT_PROVIDER,
        "hf_model": DEFAULT_HF_MODEL,
        "model": DEFAULT_HF_MODEL,
        "ollama_model": model,
        "allowed_tasks": list(ALLOWED_TASKS),
        "forbidden_tasks": list(FORBIDDEN_TASKS),
        "limits": dict(DEFAULT_LIMITS),
        "guardrails": list(DEFAULT_GUARDRAILS),
        "stored_secret": False,
        "updated_at": now_iso(),
    }


def summarize_mini_brain(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {
        "status": value.get("status"),
        "enabled": value.get("enabled") is True,
        "available": value.get("available") is True,
        "provider": value.get("provider"),
        "hf_model": value.get("hf_model") or value.get("model"),
        "ollama_model": value.get("ollama_model"),
        "stored_secret": value.get("stored_secret") is True,
    }


def list_value(value: Any, default: list[str]) -> list[str]:
    if not isinstance(value, list):
        return list(default)
    return [str(item) for item in value if str(item).strip()]


def dict_value(value: Any, default: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return dict(default)
    return dict(value)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
