"""Local source registry for reusable provider/project configuration."""

from __future__ import annotations

import os
import re
import urllib.parse
from pathlib import Path
from typing import Any

from cli.aikit.llm import config_path, load_config, save_config
from cli.aikit.memory import redact_secrets
from cli.aikit.providers import ProviderRegistryError, load_providers, provider_or_error
from cli.aikit.runtime_paths import ROOT


SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ENV_VAR_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
URL_USERINFO_PATTERN = re.compile(r"(?i)://[^/\s:@]+(?::[^@\s/]*)?@")
SECRET_KEY_MARKERS = (
    "api_key",
    "apikey",
    "chave",
    "conn_string",
    "connection_string",
    "database_url",
    "dsn",
    "passwd",
    "password",
    "pat",
    "privatekey",
    "private_key",
    "pwd",
    "secret",
    "senha",
    "token",
)
SECRET_EXACT_KEYS = {
    "api_key",
    "apikey",
    "pat",
    "privatekey",
}
SECRET_CONFIG_KEYS = {
    "conn_string",
    "connection_string",
    "database_url",
    "db_url",
    "dsn",
}

class SourceRegistryError(ValueError):
    """Raised for user-facing source registry errors."""


class SourceConfigBlockedError(SourceRegistryError):
    """Raised when source config would persist a secret-like value."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        super().__init__(str(payload.get("message") or "source config blocked"))


def list_sources() -> dict[str, Any]:
    registry = source_registry(load_config())
    items = [public_source(item) for item in registry["items"].values()]
    items.sort(key=lambda item: item["id"])
    return {
        "kind": "sources",
        "config_path": str(config_path()),
        "items": items,
        "defaults": registry["defaults"],
        "stored_secret": any(item.get("stored_secret") for item in items),
    }


def add_source(
    source_id: str,
    *,
    provider: str | None,
    label: str | None = None,
    config_pairs: list[str] | None = None,
    env_refs: list[str] | None = None,
    env_files: list[str] | None = None,
    default_for: list[str] | None = None,
    default_for_agent: list[str] | None = None,
    set_default: bool = False,
) -> dict[str, Any]:
    if not source_id or not SOURCE_ID_PATTERN.match(source_id):
        raise SourceRegistryError("source id must use lowercase letters, numbers, dots, dashes or underscores")
    if not provider:
        raise SourceRegistryError("source add requires --provider")

    config = load_config()
    registry = source_registry(config)
    existing = registry["items"].get(source_id, {})
    if not isinstance(existing, dict):
        existing = {}
    provider_metadata = source_provider_metadata(provider)

    try:
        parsed_config = parse_config_pairs(
            config_pairs or [],
            existing.get("config") or {},
            provider=provider,
            source_id=source_id,
            provider_metadata=provider_metadata,
        )
    except SourceConfigBlockedError:
        raise
    entry = {
        "id": source_id,
        "provider": provider,
        "label": label or existing.get("label") or source_id,
        "config": parsed_config,
        "env_refs": parse_env_refs(env_refs or [], existing.get("env_refs") or {}),
        "env_files": normalize_env_files(env_files or existing.get("env_files") or []),
        "defaults": {
            "intents": sorted(set((default_for or []) + ((existing.get("defaults") or {}).get("intents") or []))),
            "agents": sorted(set((default_for_agent or []) + ((existing.get("defaults") or {}).get("agents") or []))),
        },
    }
    registry["items"][source_id] = entry
    defaults = registry["defaults"]
    if set_default:
        defaults.setdefault("providers", {})[provider] = source_id
    for intent in default_for or []:
        defaults.setdefault("intents", {})[intent] = source_id
    for agent_id in default_for_agent or []:
        defaults.setdefault("agents", {})[agent_id] = source_id

    written_path = save_config(config)
    return {
        "kind": "source-configure",
        "status": "configured",
        "source": public_source(entry),
        "defaults": defaults,
        "config_path": str(written_path),
        "stored_secret": False,
    }


def source_status(source_id: str | None = None) -> dict[str, Any]:
    registry = source_registry(load_config())
    if source_id:
        source = registry["items"].get(source_id)
        if not source:
            raise SourceRegistryError(f"source not found: {source_id}")
        items = [source_status_item(source)]
    else:
        items = [source_status_item(source) for source in registry["items"].values()]
        items.sort(key=lambda item: item["id"])
    status = "ok" if all(item["status"] == "ok" for item in items) else "partial"
    if not items:
        status = "missing"
    return {
        "kind": "source-status",
        "status": status,
        "config_path": str(config_path()),
        "items": items,
        "stored_secret": any(item.get("stored_secret") for item in items),
    }


def remove_source(source_id: str) -> dict[str, Any]:
    config = load_config()
    registry = source_registry(config)
    if source_id not in registry["items"]:
        raise SourceRegistryError(f"source not found: {source_id}")
    source = registry["items"].pop(source_id)
    for mapping in registry["defaults"].values():
        if isinstance(mapping, dict):
            for key, value in list(mapping.items()):
                if value == source_id:
                    del mapping[key]
    written_path = save_config(config)
    return {
        "kind": "source-remove",
        "status": "removed",
        "source": public_source(source),
        "config_path": str(written_path),
        "stored_secret": False,
    }


def resolve_source(
    *,
    source_id: str | None = None,
    provider: str | None = None,
    intent: str | None = None,
    agent_id: str | None = None,
) -> dict[str, Any] | None:
    registry = source_registry(load_config())
    items = registry["items"]
    if source_id:
        source = items.get(source_id)
        if not source:
            raise SourceRegistryError(f"source not found: {source_id}")
        return source

    defaults = registry["defaults"]
    for scope, key in (("agents", agent_id), ("intents", intent), ("providers", provider)):
        if not key:
            continue
        candidate_id = defaults.get(scope, {}).get(key)
        if candidate_id and candidate_id in items:
            source = items[candidate_id]
            if not provider or source.get("provider") == provider:
                return source

    candidates = [
        source
        for source in items.values()
        if (not provider or source.get("provider") == provider)
        and (not agent_id or agent_id in (source.get("defaults", {}).get("agents") or []))
    ]
    if len(candidates) == 1:
        return candidates[0]
    candidates = [source for source in items.values() if not provider or source.get("provider") == provider]
    if len(candidates) == 1:
        return candidates[0]
    return None


def extract_source_arg(args: list[str]) -> tuple[str | None, list[str]]:
    source_id: str | None = None
    cleaned: list[str] = []
    index = 0
    while index < len(args):
        item = args[index]
        if item == "--source":
            if index + 1 >= len(args):
                raise SourceRegistryError("--source requires a source id")
            source_id = args[index + 1]
            index += 2
            continue
        if item.startswith("--source="):
            source_id = item.split("=", 1)[1]
            index += 1
            continue
        cleaned.append(item)
        index += 1
    return source_id, cleaned


def apply_source_to_args(
    source: dict[str, Any] | None,
    source_contract: dict[str, Any] | None,
    args: list[str],
) -> list[str]:
    if not source:
        return args
    config = source.get("config") or {}
    result = list(args)
    for config_key, flag in source_arg_map(source_contract).items():
        value = config.get(config_key)
        if value is not None and str(value).strip() and not has_arg(result, flag):
            result.extend([flag, str(value)])
    return result


def source_env(source: dict[str, Any] | None, source_contract: dict[str, Any] | None = None) -> dict[str, str]:
    if not source:
        return {}
    provider_metadata = source_provider_metadata(str(source.get("provider") or ""))
    unsafe_keys = set(unsafe_source_config_keys(dict(source.get("config") or {}), provider_metadata=provider_metadata))
    env_map = source_env_map(source_contract)
    env: dict[str, str] = {}
    for key, value in (source.get("config") or {}).items():
        if str(key) in unsafe_keys:
            continue
        env_name = env_map.get(str(key))
        if env_name and value is not None:
            env[env_name] = str(value)
    for key, env_ref in (source.get("env_refs") or {}).items():
        if env_ref in os.environ:
            env_name = env_map.get(str(key)) or str(key)
            env[env_name] = os.environ[env_ref]
    return env


def source_arg_map(source_contract: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(source_contract, dict):
        return {}
    mapping = source_contract.get("args") if isinstance(source_contract.get("args"), dict) else {}
    return {
        str(key): str(value)
        for key, value in mapping.items()
        if str(key).strip() and str(value).startswith("--")
    }


def source_env_map(source_contract: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(source_contract, dict):
        return {}
    mapping = source_contract.get("env") if isinstance(source_contract.get("env"), dict) else {}
    return {
        str(key): str(value)
        for key, value in mapping.items()
        if str(key).strip() and ENV_VAR_NAME_PATTERN.match(str(value))
    }


def public_source(source: dict[str, Any]) -> dict[str, Any]:
    config = dict(source.get("config") or {})
    provider_metadata = source_provider_metadata(str(source.get("provider") or ""))
    unsafe_config_keys = unsafe_source_config_keys(config, provider_metadata=provider_metadata)
    return {
        "id": source.get("id"),
        "provider": source.get("provider"),
        "label": source.get("label"),
        "config": redacted_source_config(config, unsafe_config_keys),
        "env_refs": dict(source.get("env_refs") or {}),
        "env_files": list(source.get("env_files") or []),
        "defaults": {
            "intents": list((source.get("defaults") or {}).get("intents") or []),
            "agents": list((source.get("defaults") or {}).get("agents") or []),
        },
        "unsafe_config_keys": unsafe_config_keys,
        "stored_secret": bool(unsafe_config_keys),
    }


def source_registry(config: dict[str, Any]) -> dict[str, Any]:
    registry = config.setdefault("sources", {})
    if not isinstance(registry, dict):
        registry = {}
        config["sources"] = registry
    items = registry.setdefault("items", {})
    if not isinstance(items, dict):
        items = {}
        registry["items"] = items
    defaults = registry.setdefault("defaults", {})
    if not isinstance(defaults, dict):
        defaults = {}
        registry["defaults"] = defaults
    for key in ("providers", "intents", "agents"):
        if not isinstance(defaults.get(key), dict):
            defaults[key] = {}
    return {"items": items, "defaults": defaults}


def parse_config_pairs(
    pairs: list[str],
    existing: dict[str, Any],
    *,
    provider: str | None = None,
    source_id: str | None = None,
    provider_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = dict(existing)
    for pair in pairs:
        key, value = split_pair(pair, "--config")
        validate_non_secret_source_config(
            key,
            value,
            provider=provider,
            source_id=source_id,
            provider_metadata=provider_metadata,
        )
        result[key] = value
    unsafe_keys = unsafe_source_config_keys(result, provider_metadata=provider_metadata)
    if unsafe_keys:
        formatted = ", ".join(unsafe_keys)
        raise SourceRegistryError(
            f"source config contains unsafe key(s): {formatted}. Remove this source and recreate it using --env for credentials."
        )
    return result


def parse_env_refs(refs: list[str], existing: dict[str, str]) -> dict[str, str]:
    result = dict(existing)
    for ref in refs:
        key, value = split_pair(ref, "--env")
        if not ENV_VAR_NAME_PATTERN.match(key) or not ENV_VAR_NAME_PATTERN.match(value):
            raise SourceRegistryError("--env must use ENV_FIELD=ENV_VAR_NAME and cannot contain raw secret values")
        result[key] = value
    return result


def split_pair(value: str, flag: str) -> tuple[str, str]:
    if "=" not in value:
        raise SourceRegistryError(f"{flag} requires KEY=VALUE")
    key, raw = value.split("=", 1)
    key = key.strip()
    raw = raw.strip()
    if not key or not raw:
        raise SourceRegistryError(f"{flag} requires KEY=VALUE")
    return key, raw


def normalize_env_files(paths: list[str]) -> list[str]:
    return [str(Path(path).expanduser()) for path in paths]


def source_status_item(source: dict[str, Any]) -> dict[str, Any]:
    env_refs = source.get("env_refs") or {}
    present = sorted(key for key, env_name in env_refs.items() if os.environ.get(env_name))
    missing = sorted(key for key, env_name in env_refs.items() if not os.environ.get(env_name))
    item = public_source(source)
    status = "ok" if not missing else "missing"
    if item.get("stored_secret"):
        status = "unsafe"
    item.update(
        {
            "status": status,
            "detected_env_refs": present,
            "missing_env_refs": missing,
            "next_steps": unsafe_source_next_steps(item.get("unsafe_config_keys") or []),
        }
    )
    return item


def has_arg(args: list[str], flag: str) -> bool:
    prefix = f"{flag}="
    return any(item == flag or item.startswith(prefix) for item in args)


def validate_non_secret_source_config(
    key: str,
    value: str,
    *,
    provider: str | None = None,
    source_id: str | None = None,
    provider_metadata: dict[str, Any] | None = None,
) -> None:
    assessment = unsafe_source_config_assessment(key, value, provider_metadata=provider_metadata)
    if not assessment:
        return
    raise SourceConfigBlockedError(
        blocked_source_config_payload(
            source_id=source_id,
            provider=provider,
            field=key,
            reason=str(assessment["reason"]),
            detail=str(assessment["detail"]),
        )
    )


def unsafe_source_config_keys(config: dict[str, Any], *, provider_metadata: dict[str, Any] | None = None) -> list[str]:
    return sorted(
        str(key)
        for key, value in config.items()
        if unsafe_source_config_reason(str(key), str(value), provider_metadata=provider_metadata)
    )


def unsafe_source_config_reason(key: str, value: str, *, provider_metadata: dict[str, Any] | None = None) -> str | None:
    assessment = unsafe_source_config_assessment(key, value, provider_metadata=provider_metadata)
    return str(assessment["detail"]) if assessment else None


def unsafe_source_config_assessment(
    key: str,
    value: str,
    *,
    provider_metadata: dict[str, Any] | None = None,
) -> dict[str, str] | None:
    if provider_secret_field(key, provider_metadata):
        return {"reason": "provider-secret-field", "detail": "is declared as secret by provider metadata"}
    if is_sensitive_config_key(key):
        return {"reason": "secret-like-config-value", "detail": "may contain secrets"}
    if value_contains_embedded_secret(value):
        return {"reason": "secret-like-config-value", "detail": "contains a secret-like value"}
    if url_contains_userinfo(value):
        return {"reason": "secret-like-config-value", "detail": "contains credentials embedded in a URL"}
    return None


def blocked_source_config_payload(
    *,
    source_id: str | None,
    provider: str | None,
    field: str,
    reason: str,
    detail: str,
) -> dict[str, Any]:
    env_key = suggested_env_key(field)
    message = f"--config {field}=... {detail}; use --env {env_key}=LOCAL_ENV_NAME instead."
    return {
        "kind": "source-configure",
        "status": "blocked",
        "ok": False,
        "reason": reason,
        "field": field,
        "provider": provider,
        "source_id": source_id,
        "message": message,
        "next_steps": [f"Use `--env {env_key}=LOCAL_ENV_NAME` instead of storing raw values."],
        "stored_secret": False,
        "exit_code": 2,
    }


def source_provider_metadata(provider_id: str | None) -> dict[str, Any]:
    if not provider_id:
        return {}
    try:
        return provider_or_error(load_providers(ROOT), provider_id)
    except ProviderRegistryError:
        return {}


def provider_secret_field(key: str, provider_metadata: dict[str, Any] | None) -> bool:
    if not isinstance(provider_metadata, dict):
        return False
    exact = str(key)
    normalized = normalize_secret_key(key)
    for field in provider_metadata.get("config_fields", []) or []:
        if not isinstance(field, dict) or field.get("secret") is not True:
            continue
        name = str(field.get("name") or "")
        if exact == name or normalized == normalize_secret_key(name):
            return True
    for method in provider_metadata.get("auth_methods", []) or []:
        if not isinstance(method, dict):
            continue
        for secret_field in method.get("secret_fields", []) or []:
            name = str(secret_field or "")
            if exact == name or normalized == normalize_secret_key(name):
                return True
    return False


def is_sensitive_config_key(key: str) -> bool:
    normalized = normalize_secret_key(key)
    if normalized in SECRET_CONFIG_KEYS:
        return True
    if normalized in SECRET_EXACT_KEYS:
        return True
    return any(secret_key_marker_matches(normalized, marker) for marker in SECRET_KEY_MARKERS)


def secret_key_marker_matches(normalized_key: str, marker: str) -> bool:
    if marker in SECRET_EXACT_KEYS:
        return normalized_key == marker
    return (
        normalized_key == marker
        or normalized_key.startswith(f"{marker}_")
        or normalized_key.endswith(f"_{marker}")
        or f"_{marker}_" in normalized_key
    )


def value_contains_embedded_secret(value: str) -> bool:
    return redact_secrets(value) != value


def url_contains_userinfo(value: str) -> bool:
    if URL_USERINFO_PATTERN.search(value):
        return True
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError:
        return False
    return bool(parsed.username or parsed.password)


def redacted_source_config(config: dict[str, Any], unsafe_keys: list[str]) -> dict[str, Any]:
    unsafe = set(unsafe_keys)
    return {
        key: "[REDACTED_SECRET]" if str(key) in unsafe else value
        for key, value in config.items()
    }


def unsafe_source_next_steps(unsafe_keys: list[str]) -> list[str]:
    if not unsafe_keys:
        return []
    return [
        "Remove this source with `agent source remove <source-id>`.",
        "Recreate it using `--config` only for non-secret values and `--env PROVIDER_FIELD=LOCAL_ENV_NAME` for credentials.",
    ]


def suggested_env_key(key: str) -> str:
    normalized = normalize_secret_key(key)
    if normalized in {"conn_string", "connection_string", "database_url", "db_url", "dsn"}:
        return "PROVIDER_CONNECTION_STRING"
    return normalize_secret_key(key).upper()


def normalize_secret_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
