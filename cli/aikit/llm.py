"""LLM backend registry and local configuration helpers for agent."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cli.aikit.app_home import app_home, config_path as app_config_path, ensure_app_home
from cli.aikit.identity import host_cli_prompt, identity_system_prompt


@dataclass(frozen=True)
class LlmBackend:
    id: str
    display_name: str
    kind: str
    auth: str
    api_key_env: str | None = None
    base_url_env: str | None = None
    model_env: str | None = None
    default_base_url: str | None = None
    default_model: str | None = None
    command: str | None = None
    notes: str | None = None


BACKENDS: dict[str, LlmBackend] = {
    "openai": LlmBackend(
        id="openai",
        display_name="OpenAI API",
        kind="openai-compatible",
        auth="api-key-env",
        api_key_env="OPENAI_API_KEY",
        base_url_env="OPENAI_BASE_URL",
        model_env="OPENAI_MODEL",
        default_base_url="https://api.openai.com/v1",
        default_model="gpt-5",
        notes="Uses the official OpenAI API or an OpenAI-compatible base URL.",
    ),
    "anthropic": LlmBackend(
        id="anthropic",
        display_name="Anthropic API",
        kind="anthropic",
        auth="api-key-env",
        api_key_env="ANTHROPIC_API_KEY",
        base_url_env="ANTHROPIC_BASE_URL",
        model_env="ANTHROPIC_MODEL",
        default_base_url="https://api.anthropic.com/v1",
        default_model="claude-sonnet-4",
        notes="Uses the official Anthropic API.",
    ),
    "openrouter": LlmBackend(
        id="openrouter",
        display_name="OpenRouter API",
        kind="openai-compatible",
        auth="api-key-env",
        api_key_env="OPENROUTER_API_KEY",
        base_url_env="OPENROUTER_BASE_URL",
        model_env="OPENROUTER_MODEL",
        default_base_url="https://openrouter.ai/api/v1",
        default_model="openai/gpt-5",
        notes="Uses OpenRouter through its OpenAI-compatible API.",
    ),
    "ollama": LlmBackend(
        id="ollama",
        display_name="Ollama local",
        kind="openai-compatible",
        auth="none",
        base_url_env="OLLAMA_BASE_URL",
        model_env="OLLAMA_MODEL",
        default_base_url="http://localhost:11434/v1",
        default_model="qwen3:0.6b",
        notes="Uses a local Ollama server through an OpenAI-compatible endpoint.",
    ),
    "codex-cli": LlmBackend(
        id="codex-cli",
        display_name="Codex CLI",
        kind="host-cli",
        auth="external-login",
        command="codex",
        notes="Uses the official Codex CLI authentication outside AI DevKit.",
    ),
    "claude-code": LlmBackend(
        id="claude-code",
        display_name="Claude Code",
        kind="host-cli",
        auth="external-login",
        command="claude",
        notes="Uses the official Claude Code authentication outside AI DevKit.",
    ),
}

ENV_VAR_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DEFAULT_AGENT_TIMEOUT_SECONDS = 120
DEFAULT_FALLBACK_ORDER = ("claude-code", "codex-cli", "openai", "anthropic", "openrouter", "ollama")


def config_home() -> Path:
    return app_home()


def config_path() -> Path:
    return app_config_path()


def empty_config() -> dict[str, Any]:
    return {"version": 1, "llm": {"default": None, "backends": {}}}


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return empty_config()
    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return empty_config()
    if not isinstance(data, dict):
        return empty_config()
    data.setdefault("version", 1)
    llm = data.setdefault("llm", {})
    if not isinstance(llm, dict):
        data["llm"] = {"default": None, "backends": {}}
    else:
        llm.setdefault("default", None)
        if not isinstance(llm.get("backends"), dict):
            llm["backends"] = {}
    return data


def save_config(config: dict[str, Any]) -> Path:
    ensure_app_home()
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return path


def backend_or_error(backend_id: str) -> LlmBackend:
    if backend_id not in BACKENDS:
        available = ", ".join(sorted(BACKENDS))
        raise ValueError(f"unknown LLM backend: {backend_id}. available: {available}")
    return BACKENDS[backend_id]


def list_backends() -> dict[str, Any]:
    config = load_config()
    default_backend = config.get("llm", {}).get("default")
    configured = set(config.get("llm", {}).get("backends", {}))
    preference = llm_preference(config)
    from cli.aikit.decision_store import get_decision

    return {
        "kind": "llm-backends",
        "config_path": str(config_path()),
        "default": default_backend,
        "preference": preference,
        "items": [
            {
                "id": backend.id,
                "display_name": backend.display_name,
                "kind": backend.kind,
                "auth": backend.auth,
                "configured": backend.id in configured,
                "default": backend.id == default_backend,
                "api_key_env": backend.api_key_env,
                "base_url_env": backend.base_url_env,
                "model_env": backend.model_env,
                "default_base_url": backend.default_base_url,
                "default_model": backend.default_model,
                "command": backend.command,
                "notes": backend.notes,
                "decision": get_decision("llms", backend.id),
                "enabled": not bool((get_decision("llms", backend.id) or {}).get("state") in {"disabled_by_user", "denied_by_user"}),
            }
            for backend in BACKENDS.values()
        ],
    }


def configure_backend(
    backend_id: str,
    *,
    api_key_env: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    command: str | None = None,
    set_default: bool = False,
) -> dict[str, Any]:
    backend = backend_or_error(backend_id)
    config = load_config()
    llm = config.setdefault("llm", {"default": None, "backends": {}})
    backends = llm.setdefault("backends", {})

    existing = backends.get(backend.id, {})
    if not isinstance(existing, dict):
        existing = {}
    if api_key_env and not is_env_var_name(api_key_env):
        raise ValueError("--api-key-env must be an environment variable name, not a raw secret value")

    entry: dict[str, Any] = {
        "kind": backend.kind,
        "auth": backend.auth,
    }
    if backend.auth == "api-key-env":
        entry["api_key_ref"] = f"env:{api_key_env or existing.get('api_key_env') or backend.api_key_env}"
        entry["api_key_env"] = api_key_env or existing.get("api_key_env") or backend.api_key_env
    if backend.default_base_url or base_url:
        entry["base_url"] = base_url or existing.get("base_url") or env_value(backend.base_url_env) or backend.default_base_url
    if backend.default_model or model:
        entry["model"] = model or existing.get("model") or env_value(backend.model_env) or backend.default_model
    if backend.kind == "host-cli":
        entry["command"] = command or existing.get("command") or backend.command
    if backend.id == "ollama":
        entry["base_url"] = base_url or existing.get("base_url") or env_value(backend.base_url_env) or backend.default_base_url
        entry["model"] = model or existing.get("model") or env_value(backend.model_env) or backend.default_model

    backends[backend.id] = entry
    if set_default:
        llm["default"] = backend.id

    written_path = save_config(config)
    return {
        "kind": "llm-configure",
        "status": "configured",
        "backend": backend.id,
        "default": llm.get("default"),
        "config_path": str(written_path),
        "stored_secret": False,
        "config": redact_config(entry),
    }


def set_default_backend(backend_id: str) -> dict[str, Any]:
    backend = backend_or_error(backend_id)
    config = load_config()
    llm = config.setdefault("llm", {"default": None, "backends": {}})
    backends = llm.setdefault("backends", {})
    if backend.id not in backends:
        backends[backend.id] = default_backend_config(backend)
    llm["default"] = backend.id
    written_path = save_config(config)
    return {
        "kind": "llm-default",
        "status": "configured",
        "backend": backend.id,
        "default": backend.id,
        "config_path": str(written_path),
    }


def llm_preference(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    llm = config.get("llm") if isinstance(config.get("llm"), dict) else {}
    raw_preference = llm.get("preference") if isinstance(llm.get("preference"), dict) else {}
    primary = raw_preference.get("primary") or llm.get("default")
    order = raw_preference.get("order") if isinstance(raw_preference.get("order"), list) else None
    normalized_order = normalize_backend_order(order or DEFAULT_FALLBACK_ORDER)
    if primary and primary in BACKENDS:
        normalized_order = [primary, *[item for item in normalized_order if item != primary]]
    return {
        "kind": "llm-preference",
        "status": "ok",
        "config_path": str(config_path()),
        "primary": primary,
        "order": normalized_order,
        "fallback_enabled": bool(raw_preference.get("fallback_enabled", True)),
    }


def set_llm_preference(
    *,
    primary: str | None = None,
    order: str | list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    config = load_config()
    llm = config.setdefault("llm", {"default": None, "backends": {}})
    backends = llm.setdefault("backends", {})
    preference = llm.setdefault("preference", {})
    if not isinstance(preference, dict):
        preference = {}
        llm["preference"] = preference

    if primary:
        backend = backend_or_error(primary)
        backends.setdefault(backend.id, default_backend_config(backend))
        llm["default"] = backend.id
        preference["primary"] = backend.id
    if order is not None:
        preference["order"] = normalize_backend_order(order)
    preference.setdefault("fallback_enabled", True)
    written_path = save_config(config)
    payload = llm_preference(config)
    payload.update({"status": "configured", "config_path": str(written_path), "stored_secret": False})
    return payload


def normalize_backend_order(order: str | list[str] | tuple[str, ...]) -> list[str]:
    raw_items = order.split(",") if isinstance(order, str) else list(order)
    normalized: list[str] = []
    for raw_item in raw_items:
        backend_id = str(raw_item).strip()
        if not backend_id:
            continue
        backend_or_error(backend_id)
        if backend_id not in normalized:
            normalized.append(backend_id)
    for backend_id in DEFAULT_FALLBACK_ORDER:
        if backend_id not in normalized:
            normalized.append(backend_id)
    return normalized


def default_backend_config(backend: LlmBackend) -> dict[str, Any]:
    entry: dict[str, Any] = {"kind": backend.kind, "auth": backend.auth}
    if backend.auth == "api-key-env":
        entry["api_key_ref"] = f"env:{backend.api_key_env}"
        entry["api_key_env"] = backend.api_key_env
    if backend.default_base_url:
        entry["base_url"] = backend.default_base_url
    if backend.default_model:
        entry["model"] = backend.default_model
    if backend.command:
        entry["command"] = backend.command
    return entry


def doctor_backends(backend_id: str | None = None) -> dict[str, Any]:
    config = load_config()
    if backend_id:
        backend_or_error(backend_id)
        ids = [backend_id]
    else:
        ids = list(BACKENDS)

    checks = [doctor_backend(BACKENDS[item], config) for item in ids]
    status = "ok"
    if any(item["status"] == "missing" for item in checks):
        status = "partial" if not backend_id else "missing"
    if any(item["status"] == "error" for item in checks):
        status = "error"

    return {
        "kind": "llm-doctor",
        "status": status,
        "config_path": str(config_path()),
        "default": config.get("llm", {}).get("default"),
        "items": checks,
    }


def doctor_backend(backend: LlmBackend, config: dict[str, Any]) -> dict[str, Any]:
    configured = config.get("llm", {}).get("backends", {}).get(backend.id, {})
    if not isinstance(configured, dict):
        configured = {}

    if backend.kind == "host-cli":
        command = configured.get("command") or backend.command
        binary = shutil.which(command or "")
        version = read_command_version(binary) if binary else None
        return {
            "id": backend.id,
            "display_name": backend.display_name,
            "kind": backend.kind,
            "status": "ok" if binary else "missing",
            "configured": bool(configured),
            "command": command,
            "binary": binary,
            "version": version,
            "auth_status": "external",
            "message": (
                "Host CLI found; authentication is managed by the official CLI."
                if binary
                else "Host CLI command not found in PATH."
            ),
        }

    if backend.auth == "none":
        env_base_url = env_value(backend.base_url_env)
        base_url = configured.get("base_url") or env_base_url or backend.default_base_url
        model = configured.get("model") or env_value(backend.model_env) or backend.default_model
        binary = shutil.which(backend.id) if backend.id == "ollama" else None
        local_available = bool(configured or env_base_url or binary)
        return {
            "id": backend.id,
            "display_name": backend.display_name,
            "kind": backend.kind,
            "status": "ok" if local_available else "missing",
            "configured": bool(configured),
            "base_url": base_url,
            "model": model,
            "binary": binary,
            "health": "unchecked",
            "message": (
                "Local backend configured; daemon health is not probed by default."
                if local_available
                else "Local backend is not configured and no local binary was found in PATH."
            ),
        }

    api_key_env = configured.get("api_key_env") or backend.api_key_env
    api_key_present = bool(api_key_env and os.environ.get(api_key_env))
    base_url = configured.get("base_url") or env_value(backend.base_url_env) or backend.default_base_url
    model = configured.get("model") or env_value(backend.model_env) or backend.default_model
    return {
        "id": backend.id,
        "display_name": backend.display_name,
        "kind": backend.kind,
        "status": "ok" if api_key_present else "missing",
        "configured": bool(configured),
        "api_key_ref": f"env:{api_key_env}" if api_key_env else None,
        "api_key_present": api_key_present,
        "base_url": base_url,
        "model": model,
        "message": (
            "API key environment variable is available."
            if api_key_present
            else "API key environment variable is not available in this process."
        ),
    }


def resolve_backend(requested: str | None = None) -> dict[str, Any] | None:
    config = load_config()
    if requested:
        backend_or_error(requested)
        return doctor_backend(BACKENDS[requested], config)

    for backend_id in candidate_backend_ids(config=config, allow_fallback=True):
        check = doctor_backend(BACKENDS[backend_id], config)
        if check.get("status") == "ok":
            return check

    return None


def candidate_backend_ids(
    *,
    config: dict[str, Any],
    requested: str | None = None,
    allow_fallback: bool = True,
) -> list[str]:
    if requested:
        backend_or_error(requested)
        return [requested]
    llm = config.get("llm") if isinstance(config.get("llm"), dict) else {}
    configured = llm.get("backends") if isinstance(llm.get("backends"), dict) else {}
    configured_ids = [backend_id for backend_id in configured if backend_id in BACKENDS]
    if not configured_ids:
        return []
    from cli.aikit.decision_store import is_disabled

    configured_ids = [backend_id for backend_id in configured_ids if not is_disabled("llms", backend_id)]
    if not configured_ids:
        return []
    preference = llm_preference(config)
    ordered = [backend_id for backend_id in preference["order"] if backend_id in configured_ids]
    for backend_id in configured_ids:
        if backend_id not in ordered:
            ordered.append(backend_id)
    return ordered if allow_fallback else ordered[:1]


def invoke_agent_prompt(
    prompt: str,
    requested: str | None = None,
    *,
    public_name: str = "Agent DevKit",
    allow_fallback: bool = True,
) -> dict[str, Any]:
    config = load_config()
    candidate_ids = candidate_backend_ids(config=config, requested=requested, allow_fallback=allow_fallback)
    if not candidate_ids:
        return {
            "kind": "agent",
            "status": "blocked",
            "ok": False,
            "requires_llm": True,
            "llm_backend": requested,
            "llm_backend_attempts": [],
            "llm_fallback_enabled": allow_fallback,
            "prompt_received": True,
            "prompt_length": len(prompt),
            "message": "agent requires a configured LLM backend for natural-language tasks.",
            "next_steps": [
                "Use `agent run <agent> <capability>` for deterministic execution without LLM.",
                "Configure a backend with `agent llm configure <backend> --set-default`.",
                "Inspect available backends with `agent llm list` and their status with `agent llm doctor`.",
            ],
            "exit_code": 2,
        }

    attempts: list[dict[str, Any]] = []
    last_error: str | None = None
    for backend_id in candidate_ids:
        backend = doctor_backend(BACKENDS[backend_id], config)
        attempt = {"id": backend_id, "status": backend.get("status")}
        attempts.append(attempt)
        if backend.get("status") != "ok":
            attempt["message"] = backend.get("message")
            continue
        try:
            response = invoke_resolved_backend(backend, prompt, public_name=public_name)
        except LlmPolicyError as exc:
            attempt["status"] = "policy-blocked"
            attempt["message"] = str(exc)
            return failed_agent_payload(
                prompt,
                backend=backend,
                attempts=attempts,
                message=str(exc),
                policy_error=True,
                allow_fallback=allow_fallback,
            )
        except LlmInvocationError as exc:
            attempt["status"] = "failed"
            attempt["message"] = str(exc)
            last_error = str(exc)
            if requested or not allow_fallback:
                break
            continue
        attempt["status"] = "ok"
        return {
            "kind": "agent",
            "status": "ok",
            "ok": True,
            "requires_llm": True,
            "llm_backend": backend["id"],
            "llm_backend_status": backend["status"],
            "llm_backend_attempts": attempts,
            "llm_fallback_enabled": allow_fallback,
            "llm_fallback_used": attempts[0]["id"] != backend["id"],
            "prompt_received": True,
            "prompt_length": len(prompt),
            "response": response,
        }

    if last_error:
        return failed_agent_payload(
            prompt,
            backend={"id": attempts[-1]["id"], "status": attempts[-1].get("status")},
            attempts=attempts,
            message=last_error,
            policy_error=False,
            allow_fallback=allow_fallback,
        )
    return {
        "kind": "agent",
        "status": "blocked",
        "ok": False,
        "requires_llm": True,
        "llm_backend": requested,
        "llm_backend_attempts": attempts,
        "llm_fallback_enabled": allow_fallback,
        "prompt_received": True,
        "prompt_length": len(prompt),
        "message": "agent did not find an available configured LLM backend.",
        "next_steps": [
            "Run `agent llm doctor` to verify configured backends.",
            "Configure a backend with `agent llm configure <backend> --set-default`.",
            "Adjust fallback order with `agent llm preference set --primary <backend>`.",
        ],
        "exit_code": 2,
    }


def failed_agent_payload(
    prompt: str,
    *,
    backend: dict[str, Any],
    attempts: list[dict[str, Any]],
    message: str,
    policy_error: bool,
    allow_fallback: bool,
) -> dict[str, Any]:
    return {
        "kind": "agent",
        "status": "failed",
        "ok": False,
        "requires_llm": True,
        "llm_backend": backend.get("id"),
        "llm_backend_status": backend.get("status"),
        "llm_backend_attempts": attempts,
        "llm_fallback_enabled": allow_fallback,
        "llm_policy_error": policy_error,
        "prompt_received": True,
        "prompt_length": len(prompt),
        "message": message,
        "next_steps": [
            "Run `agent llm doctor` to verify the selected backend.",
            "Use `agent run <agent> <capability>` when deterministic execution is enough.",
        ],
        "exit_code": 1,
    }


class LlmInvocationError(RuntimeError):
    """Raised for safe, user-facing LLM invocation errors."""


class LlmPolicyError(LlmInvocationError):
    """Raised when the backend rejects content for policy or safety reasons."""


def invoke_resolved_backend(backend: dict[str, Any], prompt: str, *, public_name: str = "Agent DevKit") -> str:
    kind = backend.get("kind")
    backend_id = backend.get("id")
    if kind == "openai-compatible":
        return invoke_openai_compatible(backend, prompt, public_name=public_name)
    if kind == "anthropic":
        return invoke_anthropic(backend, prompt, public_name=public_name)
    if kind == "host-cli" and backend_id == "codex-cli":
        return invoke_host_cli(
            [
                str(backend.get("command") or "codex"),
                "exec",
                "--skip-git-repo-check",
                "--ephemeral",
                host_cli_prompt(prompt, name=public_name),
            ]
        )
    if kind == "host-cli" and backend_id == "claude-code":
        return invoke_host_cli([str(backend.get("command") or "claude"), "--print", "--permission-mode", "plan", host_cli_prompt(prompt, name=public_name)])
    raise LlmInvocationError(f"LLM backend is not invokable by agent yet: {backend_id}")


def invoke_openai_compatible(backend: dict[str, Any], prompt: str, *, public_name: str = "Agent DevKit") -> str:
    base_url = str(backend.get("base_url") or "").rstrip("/")
    model = str(backend.get("model") or "")
    if not base_url or not model:
        raise LlmInvocationError("OpenAI-compatible backend is missing base_url or model.")
    headers = {"Content-Type": "application/json"}
    api_key = api_key_from_ref(backend.get("api_key_ref"))
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": identity_system_prompt(name=public_name),
            },
            {"role": "user", "content": prompt},
        ],
    }
    payload = post_json(f"{base_url}/chat/completions", headers, body)
    try:
        return str(payload["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise LlmInvocationError("OpenAI-compatible backend returned an unexpected response shape.") from exc


def invoke_anthropic(backend: dict[str, Any], prompt: str, *, public_name: str = "Agent DevKit") -> str:
    api_key = api_key_from_ref(backend.get("api_key_ref"))
    if not api_key:
        raise LlmInvocationError("Anthropic backend is missing an API key environment variable.")
    model = str(backend.get("model") or "")
    if not model:
        raise LlmInvocationError("Anthropic backend is missing model.")
    base_url = str(backend.get("base_url") or "https://api.anthropic.com/v1").rstrip("/")
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": model,
        "max_tokens": 1024,
        "system": identity_system_prompt(name=public_name),
        "messages": [{"role": "user", "content": prompt}],
    }
    payload = post_json(f"{base_url}/messages", headers, body)
    try:
        parts = payload["content"]
        return "\n".join(str(part.get("text", "")).strip() for part in parts if isinstance(part, dict)).strip()
    except (KeyError, TypeError) as exc:
        raise LlmInvocationError("Anthropic backend returned an unexpected response shape.") from exc


def invoke_host_cli(command: list[str]) -> str:
    try:
        process = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=DEFAULT_AGENT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LlmInvocationError("Host CLI backend could not be executed.") from exc
    if process.returncode != 0:
        message = (process.stderr or process.stdout or "Host CLI backend failed.").strip()
        raise LlmInvocationError(redact_known_secrets(message))
    return (process.stdout or "").strip()


def post_json(url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_AGENT_TIMEOUT_SECONDS) as response:  # noqa: S310 - user-configured backend URL.
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw_error = ""
        try:
            raw_error = exc.read().decode("utf-8", errors="replace")
        except OSError:
            raw_error = ""
        if is_policy_error(exc.code, raw_error):
            raise LlmPolicyError(f"LLM backend policy error: {exc.code}") from exc
        raise LlmInvocationError(f"LLM backend HTTP error: {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise LlmInvocationError(f"LLM backend connection failed: {exc.reason}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LlmInvocationError("LLM backend returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise LlmInvocationError("LLM backend returned a non-object JSON payload.")
    if payload_has_policy_error(payload):
        raise LlmPolicyError("LLM backend returned a policy error.")
    return payload


def is_policy_error(status_code: int, body: str) -> bool:
    if status_code not in {400, 403}:
        return False
    return any(marker in body.lower() for marker in ("policy", "safety", "content_filter", "content filter", "not allowed"))


def payload_has_policy_error(payload: dict[str, Any]) -> bool:
    error = payload.get("error")
    if not isinstance(error, dict):
        return False
    text = json.dumps(error, ensure_ascii=False).lower()
    return any(marker in text for marker in ("policy", "safety", "content_filter", "content filter", "not allowed"))


def api_key_from_ref(value: Any) -> str | None:
    ref = str(value or "")
    if not ref.startswith("env:"):
        return None
    return os.environ.get(ref.split(":", 1)[1])


def redact_known_secrets(value: str) -> str:
    redacted = value
    for key, secret in os.environ.items():
        if secret and secret in redacted and any(marker in key.upper() for marker in ("KEY", "TOKEN", "SECRET", "PASSWORD", "PAT")):
            redacted = redacted.replace(secret, "[REDACTED]")
    return redacted


def redact_config(entry: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(entry)
    redacted.pop("api_key", None)
    return redacted


def env_value(name: str | None) -> str | None:
    if not name:
        return None
    return os.environ.get(name)


def is_env_var_name(value: str) -> bool:
    return bool(ENV_VAR_NAME_PATTERN.fullmatch(value))


def read_command_version(binary: str | None) -> str | None:
    if not binary:
        return None
    for args in ([binary, "--version"], [binary, "version"]):
        try:
            process = subprocess.run(
                args,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        output = (process.stdout or process.stderr or "").strip()
        if output:
            return output.splitlines()[0]
    return None
