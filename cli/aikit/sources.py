"""Local source registry for reusable provider/project configuration."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from cli.aikit.llm import config_path, load_config, save_config


SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ENV_VAR_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

PROVIDER_CONFIG_ENV: dict[str, dict[str, str]] = {
    "azure-devops": {
        "org": "AZURE_DEVOPS_ORG",
        "organization": "AZURE_DEVOPS_ORG",
        "project": "AZURE_DEVOPS_PROJECT",
        "api_version": "AZURE_DEVOPS_API_VERSION",
    },
    "aws": {
        "profile": "AWS_PROFILE",
        "region": "AWS_REGION",
    },
    "elasticsearch": {
        "url": "ELASTICSEARCH_URL",
        "default_time_field": "ELASTICSEARCH_DEFAULT_TIME_FIELD",
    },
    "postgres": {
        "conn_string": "POSTGRES_DB_CONN_STRING",
        "database_url": "POSTGRES_DB_CONN_STRING",
    },
    "sqlserver": {
        "conn_string": "SQLSERVER_DB_CONN_STRING",
    },
    "topdesk": {
        "base_url": "TOPDESK_BASE_URL",
        "username": "TOPDESK_USERNAME",
    },
}


class SourceRegistryError(ValueError):
    """Raised for user-facing source registry errors."""


def list_sources() -> dict[str, Any]:
    registry = source_registry(load_config())
    items = [public_source(item) for item in registry["items"].values()]
    items.sort(key=lambda item: item["id"])
    return {
        "kind": "sources",
        "config_path": str(config_path()),
        "items": items,
        "defaults": registry["defaults"],
        "stored_secret": False,
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

    entry = {
        "id": source_id,
        "provider": provider,
        "label": label or existing.get("label") or source_id,
        "config": parse_config_pairs(config_pairs or [], existing.get("config") or {}),
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
        "stored_secret": False,
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


def apply_source_to_args(source: dict[str, Any] | None, agent_id: str, capability_id: str, args: list[str]) -> list[str]:
    if not source:
        return args
    config = source.get("config") or {}
    result = list(args)
    if agent_id == "azure-devops-orchestrator" and capability_id == "read-card":
        if config.get("project") and not has_arg(result, "--project"):
            result.extend(["--project", str(config["project"])])
        if config.get("fixture") and not has_arg(result, "--fixture"):
            result.extend(["--fixture", str(config["fixture"])])
    return result


def source_env(source: dict[str, Any] | None) -> dict[str, str]:
    if not source:
        return {}
    provider = str(source.get("provider") or "")
    env: dict[str, str] = {}
    for key, value in (source.get("config") or {}).items():
        env_name = PROVIDER_CONFIG_ENV.get(provider, {}).get(key)
        if env_name and value is not None:
            env[env_name] = str(value)
    for key, env_ref in (source.get("env_refs") or {}).items():
        if env_ref in os.environ:
            env[key] = os.environ[env_ref]
    return env


def public_source(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": source.get("id"),
        "provider": source.get("provider"),
        "label": source.get("label"),
        "config": dict(source.get("config") or {}),
        "env_refs": dict(source.get("env_refs") or {}),
        "env_files": list(source.get("env_files") or []),
        "defaults": {
            "intents": list((source.get("defaults") or {}).get("intents") or []),
            "agents": list((source.get("defaults") or {}).get("agents") or []),
        },
        "stored_secret": False,
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


def parse_config_pairs(pairs: list[str], existing: dict[str, Any]) -> dict[str, Any]:
    result = dict(existing)
    for pair in pairs:
        key, value = split_pair(pair, "--config")
        result[key] = value
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
    status = "ok" if not missing else "missing"
    item = public_source(source)
    item.update(
        {
            "status": status,
            "detected_env_refs": present,
            "missing_env_refs": missing,
        }
    )
    return item


def has_arg(args: list[str], flag: str) -> bool:
    prefix = f"{flag}="
    return any(item == flag or item.startswith(prefix) for item in args)
