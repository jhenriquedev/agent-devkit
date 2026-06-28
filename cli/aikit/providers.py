"""Provider registry helpers for aikit."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from cli.aikit.app_home import app_home, config_path as app_config_path, ensure_app_home
from cli.aikit.credentials import CredentialResolverError, resolve_provider_credentials


REQUIRED_PROVIDER_KEYS = {
    "id",
    "name",
    "kind",
    "status",
    "description",
    "auth_methods",
    "config_fields",
    "capabilities",
    "health_check",
    "risk",
    "fallbacks",
}
SECRET_MARKERS = ("SECRET", "TOKEN", "PASSWORD", "PAT", "API_KEY", "PRIVATE_KEY")
ENV_VAR_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ProviderRegistryError(RuntimeError):
    """Raised for provider registry errors."""


def list_providers(root: Path) -> dict[str, Any]:
    providers = [summarize_provider(provider) for provider in load_providers(root)]
    return {
        "kind": "providers",
        "items": providers,
    }


def provider_status(root: Path, provider_id: str | None = None) -> dict[str, Any]:
    return provider_status_with_credentials(root, provider_id)


def provider_status_with_credentials(
    root: Path,
    provider_id: str | None = None,
    *,
    env_files: list[Path] | None = None,
) -> dict[str, Any]:
    providers = load_providers(root)
    if provider_id:
        providers = [provider_or_error(providers, provider_id)]

    items = [
        status_for_provider(
            provider,
            env_files=effective_env_files(provider.get("id"), env_files),
        )
        for provider in providers
    ]
    status = "ok"
    if any(item["status"] == "missing" for item in items):
        status = "missing" if provider_id else "partial"
    if any(item["status"] == "error" for item in items):
        status = "error"

    return {
        "kind": "provider-status",
        "status": status,
        "provider": provider_id,
        "items": items,
    }


def provider_configure_blocked(root: Path, provider_id: str) -> dict[str, Any]:
    provider = provider_or_error(load_providers(root), provider_id)
    required = [
        field["name"]
        for field in provider.get("config_fields", []) or []
        if isinstance(field, dict) and field.get("required")
    ]
    auth_options = [
        {
            "id": method.get("id"),
            "secret_fields": list(method.get("secret_fields", []) or []),
        }
        for method in provider.get("auth_methods", []) or []
        if isinstance(method, dict)
    ]
    return {
        "kind": "provider-configure",
        "status": "blocked",
        "provider": provider["id"],
        "requires_credential_resolver": False,
        "requires_config_persistence": True,
        "message": "Provider configuration persistence is planned for activity 6/15.",
        "required_config_fields": required,
        "auth_options": auth_options,
        "next_steps": [
            "Use environment variables for now when running deterministic capabilities.",
            "Run `agent provider status <provider>` to see which fields are detected.",
        ],
        "exit_code": 2,
    }


def configure_provider(
    root: Path,
    provider_id: str,
    *,
    env_refs: list[str] | None = None,
    env_files: list[Path] | None = None,
    from_env: bool = False,
    session_only: bool = False,
) -> dict[str, Any]:
    provider = provider_or_error(load_providers(root), provider_id)
    env_refs = list(env_refs or [])
    env_files = [path.expanduser().resolve() for path in (env_files or [])]
    for env_ref in env_refs:
        if not is_env_var_name(env_ref):
            raise ProviderRegistryError("--env must be an environment variable name, not a raw value")

    if from_env:
        env_refs.extend(detect_current_env_refs(provider))
    env_refs = sorted(set(env_refs))

    if not env_refs and not env_files:
        return provider_configure_needs_input(provider)

    env_file_refs = resolve_env_file_refs(provider, env_files)
    refs = build_env_refs(provider, env_refs)
    empty_env_files = [item["path"] for item in env_file_refs if not item.get("fields")]
    if empty_env_files:
        result = provider_configure_needs_input(provider)
        result["message"] = "Credential env-file does not contain recognized fields for this provider."
        result["env_files_without_provider_fields"] = empty_env_files
        return result
    entry = {
        "provider": provider["id"],
        "refs": refs,
        "env_files": env_file_refs,
        "stored_secret": False,
    }

    if session_only:
        resolution = resolve_provider_credentials(provider, env_files=env_files)
        return {
            "kind": "provider-configure",
            "status": "session-only",
            "provider": provider["id"],
            "configured": resolution["status"] == "ok",
            "config_path": None,
            "stored_secret": False,
            "session_only": True,
            "config": entry,
        }

    config = load_runtime_config()
    providers_config = config.setdefault("providers", {})
    if not isinstance(providers_config, dict):
        providers_config = {}
        config["providers"] = providers_config
    providers_config[provider["id"]] = entry
    written_path = save_runtime_config(config)
    status = status_for_provider(provider, env_files=effective_env_files(provider["id"], []))
    return {
        "kind": "provider-configure",
        "status": "configured",
        "provider": provider["id"],
        "configured": status["status"] == "ok",
        "config_path": str(written_path),
        "stored_secret": False,
        "session_only": False,
        "config": entry,
        "provider_status": status["status"],
    }


def unset_provider_config(root: Path, provider_id: str) -> dict[str, Any]:
    provider_or_error(load_providers(root), provider_id)
    config = load_runtime_config()
    providers_config = config.setdefault("providers", {})
    removed = False
    if isinstance(providers_config, dict) and provider_id in providers_config:
        removed = True
        providers_config.pop(provider_id, None)
    written_path = save_runtime_config(config)
    return {
        "kind": "provider-unset",
        "status": "removed" if removed else "not-configured",
        "provider": provider_id,
        "config_path": str(written_path),
    }


def load_providers(root: Path) -> list[dict[str, Any]]:
    providers_dir = root / "providers"
    if not providers_dir.is_dir():
        return []
    providers = []
    for manifest_path in sorted(providers_dir.glob("*.yaml")):
        provider = load_yaml(manifest_path)
        if not isinstance(provider, dict):
            continue
        provider["_path"] = manifest_path
        providers.append(provider)
    return providers


def provider_or_error(providers: list[dict[str, Any]], provider_id: str) -> dict[str, Any]:
    for provider in providers:
        if provider.get("id") == provider_id:
            return provider
    available = ", ".join(str(provider.get("id")) for provider in providers) or "none"
    raise ProviderRegistryError(f"provider not found: {provider_id}. available: {available}")


def summarize_provider(provider: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": provider.get("id"),
        "name": provider.get("name"),
        "kind": provider.get("kind"),
        "status": provider.get("status"),
        "path": provider_path(provider),
        "description": provider.get("description"),
        "writes": bool((provider.get("risk") or {}).get("writes")),
        "fallbacks": list(provider.get("fallbacks", []) or []),
        "auth_methods": [method.get("id") for method in provider.get("auth_methods", []) or [] if isinstance(method, dict)],
        "config_fields": [field.get("name") for field in provider.get("config_fields", []) or [] if isinstance(field, dict)],
    }


def status_for_provider(provider: dict[str, Any], *, env_files: list[Path] | None = None) -> dict[str, Any]:
    errors = validate_provider_contract(provider)
    if errors:
        return {
            "id": provider.get("id"),
            "name": provider.get("name"),
            "kind": provider.get("kind"),
            "status": "error",
            "configured": False,
            "errors": errors,
        }

    config_fields = [field for field in provider.get("config_fields", []) or [] if isinstance(field, dict)]
    resolution = resolve_provider_credentials(provider, env_files=env_files)
    required_missing = resolution["required_missing"]
    auth = resolution["auth"]
    local_ready = provider.get("kind") in {"local-source", "local-tool", "local-runtime"} and not provider.get("auth_methods")

    if resolution["status"] == "missing":
        status = "missing"
    elif resolution["status"] == "unknown":
        status = "unknown"
    else:
        status = "ok"

    if local_ready:
        status = "ok"

    return {
        "id": provider.get("id"),
        "name": provider.get("name"),
        "kind": provider.get("kind"),
        "status": status,
        "configured": status == "ok",
        "detected_env": resolution["detected_env"],
        "detected_env_file": resolution["detected_env_file"],
        "missing_required_fields": required_missing,
        "auth": auth,
        "credential_resolution": {
            "status": resolution["status"],
            "env_files": resolution["env_files"],
            "supported_backends": resolution["supported_backends"],
            "secret_values_returned": resolution["secret_values_returned"],
        },
        "writes": bool((provider.get("risk") or {}).get("writes")),
        "fallbacks": list(provider.get("fallbacks", []) or []),
        "message": status_message(status, required_missing, auth),
    }


def validate_provider_contract(provider: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_PROVIDER_KEYS - set(provider))
    for key in missing:
        errors.append(f"missing required key: {key}")

    provider_id = provider.get("id")
    path = provider.get("_path")
    if isinstance(path, Path) and provider_id and path.stem != provider_id:
        errors.append(f"id {provider_id!r} does not match filename {path.name!r}")

    for field in provider.get("config_fields", []) or []:
        if not isinstance(field, dict):
            errors.append("config_fields entries must be mappings")
            continue
        name = str(field.get("name", ""))
        if not name:
            errors.append("config_fields entry missing name")
        if looks_secret(name) and field.get("secret") is not True:
            errors.append(f"config field {name} looks secret but is not marked secret: true")
        if "secret" not in field:
            errors.append(f"config field {name or '<missing>'} missing secret marker")
    return errors


def credential_resolution(root: Path, provider_id: str, *, env_files: list[Path] | None = None) -> dict[str, Any]:
    provider = provider_or_error(load_providers(root), provider_id)
    try:
        resolution = resolve_provider_credentials(provider, env_files=effective_env_files(provider_id, env_files))
    except CredentialResolverError:
        raise
    return {
        "kind": "credential-resolution",
        "provider": provider["id"],
        "status": resolution["status"],
        "missing_required_fields": resolution["required_missing"],
        "auth": resolution["auth"],
        "config_fields": resolution["config_fields"],
        "detected_env": resolution["detected_env"],
        "detected_env_file": resolution["detected_env_file"],
        "env_files": resolution["env_files"],
        "supported_backends": resolution["supported_backends"],
        "secret_values_returned": False,
    }


def status_message(status: str, missing: list[str], auth: dict[str, Any]) -> str:
    if status == "ok":
        return "Provider appears configured from local process metadata."
    if status == "unknown":
        return "Provider uses a native credential chain that cannot be fully verified without external calls."
    parts = []
    if missing:
        parts.append("missing config fields: " + ", ".join(missing))
    secret_fields = auth.get("missing_secret_fields") or []
    if secret_fields:
        parts.append("missing secret refs: " + ", ".join(secret_fields))
    return "; ".join(parts) or "Provider is not configured in the current process."


def provider_configure_needs_input(provider: dict[str, Any]) -> dict[str, Any]:
    required = [
        field["name"]
        for field in provider.get("config_fields", []) or []
        if isinstance(field, dict) and field.get("required")
    ]
    auth_options = [
        {
            "id": method.get("id"),
            "secret_fields": list(method.get("secret_fields", []) or []),
        }
        for method in provider.get("auth_methods", []) or []
        if isinstance(method, dict)
    ]
    return {
        "kind": "provider-configure",
        "status": "needs-input",
        "provider": provider["id"],
        "stored_secret": False,
        "message": "Provider configuration needs an env reference, env-file, or --from-env.",
        "required_config_fields": required,
        "auth_options": auth_options,
        "next_steps": [
            "Use `--env NAME` to persist an environment variable reference.",
            "Use `--env-file PATH` to persist a reference to an existing credential file.",
            "Use `--session-only` to validate without writing config.",
        ],
        "exit_code": 2,
    }


def effective_env_files(provider_id: Any, explicit_env_files: list[Path] | None) -> list[Path]:
    files = [path.expanduser().resolve() for path in (explicit_env_files or [])]
    if not provider_id:
        return files
    configured = load_provider_config(str(provider_id))
    for item in configured.get("env_files", []) if isinstance(configured, dict) else []:
        if isinstance(item, dict) and item.get("path"):
            path = Path(str(item["path"])).expanduser().resolve()
            if path not in files:
                files.append(path)
    return files


def resolve_env_file_refs(provider: dict[str, Any], env_files: list[Path]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for path in env_files:
        resolution = resolve_provider_credentials(provider, env_files=[path])
        names = sorted(set(resolution["detected_env_file"]))
        refs.append(
            {
                "path": str(path),
                "fields": [
                    {
                        "name": name,
                        "ref": f"env-file:{path}#{name}",
                        "secret": is_secret_name(provider, name),
                    }
                    for name in names
                ],
            }
        )
    return refs


def build_env_refs(provider: dict[str, Any], env_refs: list[str]) -> dict[str, dict[str, Any]]:
    return {
        name: {
            "ref": f"env:{name}",
            "secret": is_secret_name(provider, name),
        }
        for name in env_refs
    }


def detect_current_env_refs(provider: dict[str, Any]) -> list[str]:
    names = known_provider_field_names(provider)
    return [name for name in names if os.environ.get(name)]


def known_provider_field_names(provider: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for field in provider.get("config_fields", []) or []:
        if isinstance(field, dict) and field.get("name"):
            names.append(str(field["name"]))
    for method in provider.get("auth_methods", []) or []:
        if isinstance(method, dict):
            names.extend(str(item) for item in method.get("secret_fields", []) or [])
    names.extend(str(item) for item in (provider.get("detection", {}) or {}).get("env_any", []) or [])
    return sorted(set(names))


def is_secret_name(provider: dict[str, Any], name: str) -> bool:
    for method in provider.get("auth_methods", []) or []:
        if isinstance(method, dict) and name in {str(item) for item in method.get("secret_fields", []) or []}:
            return True
    for field in provider.get("config_fields", []) or []:
        if isinstance(field, dict) and field.get("name") == name:
            return bool(field.get("secret"))
    return looks_secret(name)


def load_provider_config(provider_id: str) -> dict[str, Any]:
    providers_config = load_runtime_config().get("providers", {})
    if not isinstance(providers_config, dict):
        return {}
    entry = providers_config.get(provider_id, {})
    return entry if isinstance(entry, dict) else {}


def runtime_config_home() -> Path:
    return app_home()


def runtime_config_path() -> Path:
    return app_config_path()


def load_runtime_config() -> dict[str, Any]:
    path = runtime_config_path()
    if not path.exists():
        return {"version": 1}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1}
    if not isinstance(data, dict):
        return {"version": 1}
    data.setdefault("version", 1)
    return data


def save_runtime_config(config: dict[str, Any]) -> Path:
    ensure_app_home()
    path = runtime_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def provider_path(provider: dict[str, Any]) -> str | None:
    path = provider.get("_path")
    if isinstance(path, Path):
        return str(path)
    return None


def looks_secret(name: str) -> bool:
    upper = name.upper()
    return any(marker in upper for marker in SECRET_MARKERS)


def is_env_var_name(value: str) -> bool:
    return bool(ENV_VAR_NAME_PATTERN.fullmatch(value))


def load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - PyYAML is part of repo requirements.
        raise ProviderRegistryError("PyYAML is required to read provider manifests") from exc

    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001 - surface manifest errors as CLI errors.
        raise ProviderRegistryError(f"provider manifest is not valid YAML: {path}: {exc}") from exc
