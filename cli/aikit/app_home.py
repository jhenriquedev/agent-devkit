"""Local AI DevKit application home and filesystem layout helpers."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any


CANONICAL_APP_HOME_ENV = "AGENT_DEVKIT_HOME"
APP_HOME_ENV = "AI_DEVKIT_CONFIG_HOME"
LEGACY_APP_HOME_ENV = "AIKIT_CONFIG_HOME"
DEFAULT_APP_HOME_NAME = ".agent-devkit"
LEGACY_DEFAULT_APP_HOME_NAME = ".ai-devkit"

APP_DIRS = (
    "bin",
    "config",
    "memory",
    "sessions",
    "tasks",
    "backups",
    "policies",
    "audit",
    "secrets",
    "cache",
    "logs",
    "state",
)


def app_home() -> Path:
    """Return the configured Agent DevKit home directory."""
    raw = os.environ.get(CANONICAL_APP_HOME_ENV) or os.environ.get(APP_HOME_ENV) or os.environ.get(LEGACY_APP_HOME_ENV)
    if raw:
        return Path(raw).expanduser().resolve()
    canonical = canonical_default_app_home()
    legacy = legacy_default_app_home()
    if canonical.exists():
        return canonical
    if legacy.exists():
        return legacy
    return canonical


def canonical_default_app_home() -> Path:
    return (Path.home() / DEFAULT_APP_HOME_NAME).resolve()


def legacy_default_app_home() -> Path:
    return (Path.home() / LEGACY_DEFAULT_APP_HOME_NAME).resolve()


def app_home_status() -> dict[str, Any]:
    explicit_env = active_home_env()
    canonical = canonical_default_app_home()
    legacy = legacy_default_app_home()
    home = app_home()
    status = "canonical"
    if explicit_env:
        status = "env"
    elif home == legacy:
        status = "legacy-default-detected"
    elif not canonical.exists() and not legacy.exists():
        status = "canonical-default"
    return {
        "kind": "app-home-status",
        "status": status,
        "home": str(home),
        "canonical_home": str(canonical),
        "legacy_home": str(legacy),
        "active_env": explicit_env,
        "canonical_exists": canonical.exists(),
        "legacy_exists": legacy.exists(),
        "migration_available": not explicit_env and legacy.exists() and not canonical.exists(),
        "migration_command": "agent config migrate-home",
    }


def active_home_env() -> dict[str, str] | None:
    for name in (CANONICAL_APP_HOME_ENV, APP_HOME_ENV, LEGACY_APP_HOME_ENV):
        value = os.environ.get(name)
        if value:
            return {"name": name, "value": str(Path(value).expanduser().resolve())}
    return None


def migrate_default_home(*, dry_run: bool = False) -> dict[str, Any]:
    source = legacy_default_app_home()
    destination = canonical_default_app_home()
    payload: dict[str, Any] = {
        "kind": "home-migration",
        "source": str(source),
        "destination": str(destination),
        "dry_run": dry_run,
        "executed": False,
    }
    if destination.exists():
        return {**payload, "status": "not-needed", "message": "Canonical Agent DevKit home already exists."}
    if not source.exists():
        return {**payload, "status": "not-needed", "message": "Legacy AI DevKit home was not found."}
    if dry_run:
        return {**payload, "status": "planned", "message": "Legacy home would be migrated to canonical Agent DevKit home."}
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        source.rename(destination)
        method = "rename"
    except OSError:
        shutil.copytree(source, destination)
        shutil.rmtree(source)
        method = "copytree"
    return {
        **payload,
        "status": "migrated",
        "executed": True,
        "method": method,
        "message": "Legacy home migrated to canonical Agent DevKit home.",
    }


def app_path(*parts: str) -> Path:
    return app_home().joinpath(*parts)


def ensure_app_home() -> Path:
    """Create the application home skeleton and return its path."""
    home = app_home()
    home.mkdir(parents=True, exist_ok=True)
    for name in APP_DIRS:
        (home / name).mkdir(parents=True, exist_ok=True)
    return home


def config_path() -> Path:
    return app_path("config.json")


def memory_home() -> Path:
    return app_path("memory")


def sessions_home() -> Path:
    return app_path("sessions")


def tasks_home() -> Path:
    return app_path("tasks")


def audit_home() -> Path:
    return app_path("audit")


def policies_home() -> Path:
    return app_path("policies")


def secrets_home() -> Path:
    return app_path("secrets")


def cache_home() -> Path:
    return app_path("cache")
