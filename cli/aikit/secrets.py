"""Safe secret reference diagnostics for Agent DevKit."""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
from pathlib import Path
from typing import Any

from cli.aikit.app_home import ensure_app_home, secrets_home
from cli.aikit.errors import DevKitError


SECRET_REF_SCHEMA_VERSION = "agent-devkit.secrets/v1"


def secrets_doctor() -> dict[str, Any]:
    return {
        "kind": "secrets-doctor",
        "schema_version": SECRET_REF_SCHEMA_VERSION,
        "status": "ok",
        "stored_values": False,
        "home": str(secrets_home()),
        "backends": secret_backends()["backends"],
        "references": load_secret_references()["references"],
        "environment": {
            "secret_like_variables_detected": len(secret_like_env_names()),
            "names": secret_like_env_names(),
            "values_redacted": True,
        },
    }


def secret_backends() -> dict[str, Any]:
    system = platform.system().lower()
    backends = [
        {"id": "env", "status": "available", "stores_values": False},
        {"id": "local-reference-file", "status": "available", "stores_values": False, "path": str(references_path())},
        {"id": "macos-keychain", "status": "available" if shutil.which("security") else "unavailable", "platform": "Darwin"},
        {"id": "windows-credential-manager", "status": "available" if system == "windows" else "unavailable", "platform": "Windows"},
        {"id": "linux-secret-service", "status": "available" if shutil.which("secret-tool") else "unavailable", "platform": "Linux"},
    ]
    return {"kind": "secret-backends", "schema_version": SECRET_REF_SCHEMA_VERSION, "status": "ok", "backends": backends}


def add_secret_reference(provider: str, key: str, *, env: str | None) -> dict[str, Any]:
    provider = require_name(provider, "provider")
    key = require_name(key, "key")
    if not env:
        raise DevKitError("secrets reference add requires --env VAR_NAME")
    data = load_secret_references()
    refs = [item for item in data["references"] if not (item["provider"] == provider and item["key"] == key)]
    reference = {"provider": provider, "key": key, "backend": "env", "env": env, "value_stored": False}
    refs.append(reference)
    data["references"] = sorted(refs, key=lambda item: (item["provider"], item["key"]))
    save_secret_references(data)
    return {"kind": "secret-reference", "status": "saved", "reference": reference, "value_stored": False}


def list_secret_references() -> dict[str, Any]:
    data = load_secret_references()
    return {"kind": "secret-references", "schema_version": SECRET_REF_SCHEMA_VERSION, "status": "ok", "references": data["references"]}


def remove_secret_reference(provider: str, key: str) -> dict[str, Any]:
    provider = require_name(provider, "provider")
    key = require_name(key, "key")
    data = load_secret_references()
    before = len(data["references"])
    data["references"] = [item for item in data["references"] if not (item["provider"] == provider and item["key"] == key)]
    save_secret_references(data)
    return {"kind": "secret-reference-remove", "status": "removed" if len(data["references"]) < before else "not-found"}


def references_path() -> Path:
    ensure_app_home()
    return secrets_home() / "references.json"


def load_secret_references() -> dict[str, Any]:
    path = references_path()
    if not path.exists():
        return {"version": 1, "references": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": 1, "references": []}
    if not isinstance(data, dict) or not isinstance(data.get("references"), list):
        return {"version": 1, "references": []}
    safe_refs = []
    for item in data["references"]:
        if isinstance(item, dict):
            safe_refs.append({key: value for key, value in item.items() if key != "value"} | {"value_stored": False})
    return {"version": 1, "references": safe_refs}


def save_secret_references(data: dict[str, Any]) -> Path:
    path = references_path()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def secret_like_env_names() -> list[str]:
    pattern = re.compile(r"(^|[_-])(API[_-]?KEY|KEY|TOKEN|SECRET|PASSWORD|PASS|PAT)([_-]|$)", re.IGNORECASE)
    return sorted(name for name in os.environ if pattern.search(name))


def require_name(value: str | None, label: str) -> str:
    if not value or not value.strip():
        raise DevKitError(f"{label} is required")
    return value.strip()
