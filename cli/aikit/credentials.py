"""Credential resolution helpers for agent providers.

The resolver reports where required values are available without returning the
values themselves. This keeps CLI output and tests safe by construction.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
from pathlib import Path
from typing import Any, Mapping


SUPPORTED_BACKENDS = ("explicit", "env", "env-file", "os-keychain", "aws-default-chain", "plain-session-only")
SECRET_MARKERS = ("SECRET", "TOKEN", "PASSWORD", "PAT", "API_KEY", "PRIVATE_KEY", "CONN_STRING", "DATABASE_URL")


class CredentialResolverError(RuntimeError):
    """Raised for safe, user-facing credential resolver errors."""


def credential_backends() -> dict[str, Any]:
    details = [
        {
            "id": "explicit",
            "status": "available",
            "stores_secret": False,
            "notes": "References supplied directly by CLI flags; raw values are rejected.",
        },
        {
            "id": "env",
            "status": "available",
            "stores_secret": False,
            "notes": "Reads values already present in the current process environment.",
        },
        {
            "id": "env-file",
            "status": "available",
            "stores_secret": False,
            "notes": "Reads a user-provided .env, JSON, YAML, or YML file by path.",
        },
        {
            "id": "os-keychain",
            "status": "available" if shutil.which("security") else "unavailable",
            "stores_secret": False,
            "notes": "macOS Keychain integration is detected via the official security CLI; secrets are not read by credential diagnostics.",
        },
        {
            "id": "aws-default-chain",
            "status": "available",
            "stores_secret": False,
            "notes": "Delegates AWS credentials to the native AWS default credential chain.",
        },
        {
            "id": "plain-session-only",
            "status": "available",
            "stores_secret": False,
            "notes": "Validates credentials for the current invocation without writing config.",
        },
    ]
    return {
        "kind": "credential-backends",
        "items": list(SUPPORTED_BACKENDS),
        "details": details,
        "stored_secret": False,
    }


def resolve_provider_credentials(
    provider: dict[str, Any],
    *,
    env: Mapping[str, str] | None = None,
    env_files: list[Path] | None = None,
    explicit: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    process_env = os.environ if env is None else env
    file_values = load_env_files(env_files or [])
    explicit_values = dict(explicit or {})
    config_fields = [field for field in provider.get("config_fields", []) or [] if isinstance(field, dict)]
    config_resolution = [
        resolve_field(str(field.get("name")), field_secret(field), explicit_values, process_env, file_values)
        for field in config_fields
        if field.get("name")
    ]
    auth = resolve_auth(provider, explicit_values, process_env, file_values)
    required_missing = [
        str(field.get("name"))
        for field in config_fields
        if field.get("name")
        and field.get("required")
        and field.get("default") is None
        and not has_value(str(field.get("name")), explicit_values, process_env, file_values)
    ]
    detected_env = sorted(
        {
            item["name"]
            for item in config_resolution + auth.get("secret_resolution", []) + detection_resolution(provider, explicit_values, process_env, file_values)
            if item.get("present") and item.get("source") == "env"
        }
    )
    detected_env_file = sorted(
        {
            item["name"]
            for item in config_resolution + auth.get("secret_resolution", []) + detection_resolution(provider, explicit_values, process_env, file_values)
            if item.get("present") and item.get("source") == "env-file"
        }
    )
    return {
        "status": resolution_status(required_missing, auth),
        "required_missing": required_missing,
        "auth": auth,
        "config_fields": config_resolution,
        "detected_env": detected_env,
        "detected_env_file": detected_env_file,
        "env_files": [str(path) for path in env_files or []],
        "supported_backends": list(SUPPORTED_BACKENDS),
        "secret_values_returned": False,
    }


def resolve_auth(
    provider: dict[str, Any],
    explicit: Mapping[str, str],
    env: Mapping[str, str],
    file_values: Mapping[str, str],
) -> dict[str, Any]:
    auth_methods = [method for method in provider.get("auth_methods", []) or [] if isinstance(method, dict)]
    if not auth_methods:
        return {"status": "ok", "method": None, "missing_secret_fields": [], "secret_resolution": []}

    all_secret_resolution: list[dict[str, Any]] = []
    for method in auth_methods:
        secret_fields = [str(item) for item in method.get("secret_fields", []) or []]
        secret_resolution = [
            resolve_field(name, True, explicit, env, file_values)
            for name in secret_fields
        ]
        all_secret_resolution.extend(secret_resolution)
        if any(item["present"] for item in secret_resolution):
            return {
                "status": "ok",
                "method": method.get("id"),
                "missing_secret_fields": [],
                "secret_resolution": secret_resolution,
            }
        if method.get("native"):
            detected = provider.get("detection", {}).get("env_any", []) or []
            if any(has_value(str(name), explicit, env, file_values) for name in detected):
                return {
                    "status": "ok",
                    "method": method.get("id"),
                    "missing_secret_fields": [],
                    "secret_resolution": secret_resolution,
                }
            return {
                "status": "unknown",
                "method": method.get("id"),
                "missing_secret_fields": [],
                "secret_resolution": secret_resolution,
            }
        if not secret_fields and method.get("id") == "none":
            return {
                "status": "ok",
                "method": method.get("id"),
                "missing_secret_fields": [],
                "secret_resolution": [],
            }
        if not secret_fields:
            detected = provider.get("detection", {}).get("env_any", []) or []
            if any(has_value(str(name), explicit, env, file_values) for name in detected):
                return {
                    "status": "ok",
                    "method": method.get("id"),
                    "missing_secret_fields": [],
                    "secret_resolution": [],
                }

    missing = sorted({item["name"] for item in all_secret_resolution if not item["present"]})
    return {
        "status": "missing",
        "method": None,
        "missing_secret_fields": missing,
        "secret_resolution": all_secret_resolution,
    }


def detection_resolution(
    provider: dict[str, Any],
    explicit: Mapping[str, str],
    env: Mapping[str, str],
    file_values: Mapping[str, str],
) -> list[dict[str, Any]]:
    names = (provider.get("detection", {}) or {}).get("env_any", []) or []
    return [resolve_field(str(name), looks_secret(str(name)), explicit, env, file_values) for name in names]


def resolve_field(
    name: str,
    secret: bool,
    explicit: Mapping[str, str],
    env: Mapping[str, str],
    file_values: Mapping[str, str],
) -> dict[str, Any]:
    source = None
    if value_present(explicit.get(name)):
        source = "explicit"
    elif value_present(env.get(name)):
        source = "env"
    elif value_present(file_values.get(name)):
        source = "env-file"
    return {
        "name": name,
        "present": source is not None,
        "source": source,
        "secret": secret,
    }


def has_value(
    name: str,
    explicit: Mapping[str, str],
    env: Mapping[str, str],
    file_values: Mapping[str, str],
) -> bool:
    return value_present(explicit.get(name)) or value_present(env.get(name)) or value_present(file_values.get(name))


def value_present(value: Any) -> bool:
    return value is not None and str(value) != ""


def resolution_status(required_missing: list[str], auth: dict[str, Any]) -> str:
    if required_missing or auth.get("status") == "missing":
        return "missing"
    if auth.get("status") == "unknown":
        return "unknown"
    return "ok"


def field_secret(field: dict[str, Any]) -> bool:
    if "secret" in field:
        return bool(field.get("secret"))
    return looks_secret(str(field.get("name", "")))


def looks_secret(name: str) -> bool:
    upper = name.upper()
    return any(marker in upper for marker in SECRET_MARKERS)


def load_env_files(paths: list[Path]) -> dict[str, str]:
    values: dict[str, str] = {}
    for path in paths:
        values.update(load_env_file(path))
    return values


def load_env_file(path: Path) -> dict[str, str]:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise CredentialResolverError(f"credential file not found: {resolved}")
    if not resolved.is_file():
        raise CredentialResolverError(f"credential file is not a file: {resolved}")
    suffix = resolved.suffix.lower()
    if suffix == ".json":
        return load_json_env_file(resolved)
    if suffix in {".yaml", ".yml"}:
        return load_yaml_env_file(resolved)
    return load_dotenv_file(resolved)


def load_json_env_file(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CredentialResolverError(f"credential JSON file is invalid: {path}: line {exc.lineno}") from exc
    if not isinstance(data, dict):
        raise CredentialResolverError(f"credential JSON file must contain an object: {path}")
    return flatten_env_mapping(data)


def load_yaml_env_file(path: Path) -> dict[str, str]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - PyYAML is part of repo requirements.
        raise CredentialResolverError("PyYAML is required to read YAML credential files") from exc
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001 - report safe path context only.
        raise CredentialResolverError(f"credential YAML file is invalid: {path}") from exc
    if not isinstance(data, dict):
        raise CredentialResolverError(f"credential YAML file must contain a mapping: {path}")
    return flatten_env_mapping(data)


def flatten_env_mapping(data: Mapping[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            continue
        if value is None:
            continue
        values[str(key)] = str(value)
    return values


def load_dotenv_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            raise CredentialResolverError(f"credential env file has invalid line {line_number}: {path}")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise CredentialResolverError(f"credential env file has empty key on line {line_number}: {path}")
        values[key] = parse_env_value(value.strip())
    return values


def parse_env_value(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = shlex.split(value, comments=False, posix=True)
    except ValueError:
        return value.strip("\"'")
    if len(parsed) == 1:
        return parsed[0]
    return value.strip("\"'")
