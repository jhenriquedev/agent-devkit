"""Local AI DevKit application home and filesystem layout helpers."""

from __future__ import annotations

import os
from pathlib import Path


APP_HOME_ENV = "AI_DEVKIT_CONFIG_HOME"
LEGACY_APP_HOME_ENV = "AIKIT_CONFIG_HOME"
DEFAULT_APP_HOME_NAME = ".ai-devkit"

APP_DIRS = (
    "bin",
    "config",
    "memory",
    "sessions",
    "tasks",
    "policies",
    "audit",
    "secrets",
    "cache",
    "logs",
    "state",
)


def app_home() -> Path:
    """Return the configured Agent DevKit home directory."""
    raw = os.environ.get(APP_HOME_ENV) or os.environ.get(LEGACY_APP_HOME_ENV)
    if raw:
        return Path(raw).expanduser().resolve()
    return (Path.home() / DEFAULT_APP_HOME_NAME).resolve()


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
