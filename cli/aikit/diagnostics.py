"""Expanded diagnostics for the AI DevKit doctor command."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from cli.aikit.llm import config_path as llm_config_path
from cli.aikit.llm import doctor_backends
from cli.aikit.lock import lock_path, lock_status, read_lock
from cli.aikit.providers import provider_status_with_credentials, runtime_config_path


def build_diagnostics(
    root: Path,
    *,
    project: Path | None,
    home: Path | None,
    runtime_checks: dict[str, bool],
    runtime_status: str,
    locks: dict[str, Any],
) -> dict[str, Any]:
    return {
        "runtime": runtime_diagnostics(root, runtime_checks, runtime_status, home),
        "locks": locks,
        "plugins": plugin_diagnostics(root, project=project, home=home),
        "providers": provider_diagnostics(root),
        "llm": llm_diagnostics(),
    }


def runtime_diagnostics(
    root: Path,
    checks: dict[str, bool],
    status: str,
    home: Path | None,
) -> dict[str, Any]:
    install_home = (home or Path(os.environ.get("AIKIT_INSTALL_HOME", str(Path.home())))).expanduser().resolve()
    return {
        "kind": "runtime-summary",
        "status": status,
        "root": str(root),
        "install_home": str(install_home),
        "config_path": str(runtime_config_path()),
        "llm_config_path": str(llm_config_path()),
        "checks": checks,
    }


def provider_diagnostics(root: Path) -> dict[str, Any]:
    try:
        payload = provider_status_with_credentials(root)
    except Exception as exc:  # noqa: BLE001 - doctor should report diagnostics, not traceback.
        return {
            "kind": "provider-summary",
            "status": "error",
            "total": 0,
            "ok": 0,
            "missing": 0,
            "error": 1,
            "items": [],
            "message": str(exc),
        }

    items = [
        {
            "id": item.get("id"),
            "kind": item.get("kind"),
            "status": item.get("status"),
            "configured": item.get("configured"),
            "writes": item.get("writes"),
            "fallbacks": item.get("fallbacks", []),
            "missing_required_fields": item.get("missing_required_fields", []),
            "missing_secret_fields": (item.get("auth") or {}).get("missing_secret_fields", []),
            "detected_env": item.get("detected_env", []),
            "detected_env_file": item.get("detected_env_file", []),
            "secret_values_returned": False,
        }
        for item in payload.get("items", [])
    ]
    return {
        "kind": "provider-summary",
        "status": payload.get("status", "unknown"),
        "total": len(items),
        "ok": count_status(items, "ok"),
        "missing": count_status(items, "missing"),
        "error": count_status(items, "error"),
        "items": items,
    }


def llm_diagnostics() -> dict[str, Any]:
    try:
        payload = doctor_backends()
    except Exception as exc:  # noqa: BLE001 - doctor should report diagnostics, not traceback.
        return {
            "kind": "llm-summary",
            "status": "error",
            "total": 0,
            "ok": 0,
            "missing": 0,
            "error": 1,
            "default": None,
            "items": [],
            "message": str(exc),
        }

    items = [
        {
            "id": item.get("id"),
            "kind": item.get("kind"),
            "status": item.get("status"),
            "configured": item.get("configured"),
            "auth_status": item.get("auth_status"),
            "api_key_ref": item.get("api_key_ref"),
            "api_key_present": item.get("api_key_present"),
            "command": item.get("command"),
            "binary": item.get("binary"),
            "model": item.get("model"),
            "health": item.get("health"),
            "message": item.get("message"),
        }
        for item in payload.get("items", [])
    ]
    return {
        "kind": "llm-summary",
        "status": payload.get("status", "unknown"),
        "total": len(items),
        "ok": count_status(items, "ok"),
        "missing": count_status(items, "missing"),
        "error": count_status(items, "error"),
        "default": payload.get("default"),
        "items": items,
    }


def plugin_diagnostics(root: Path, *, project: Path | None, home: Path | None) -> dict[str, Any]:
    install_home = (home or Path(os.environ.get("AIKIT_INSTALL_HOME", str(Path.home())))).expanduser().resolve()
    project_lock = read_lock(lock_path(project.resolve(), "project")) if project else {"exists": False}
    global_lock = read_lock(lock_path(install_home, "global"))
    source = {
        "codex": codex_source(root),
        "claude-code": claude_source(root),
        "claude-desktop": claude_desktop_source(root),
    }
    project_status = installed_plugins(project.resolve(), project_lock) if project else {}
    global_status = installed_plugins(install_home, global_lock)
    source_ok = all(item["status"] == "ok" for item in source.values())
    install_statuses = []
    if project:
        install_statuses.extend(host["status"] for host in project_status.values())
    elif any_host_declared(global_lock):
        install_statuses.extend(host["status"] for host in global_status.values())

    if not source_ok:
        status = "error"
    elif install_statuses and all(item == "ok" for item in install_statuses):
        status = "ok"
    elif install_statuses and any(item == "ok" for item in install_statuses):
        status = "partial"
    elif install_statuses:
        status = "missing"
    else:
        status = "ok"

    return {
        "kind": "plugin-summary",
        "status": status,
        "source": source,
        "global": global_status,
        "project": project_status,
    }


def codex_source(root: Path) -> dict[str, Any]:
    plugin = root / "plugins" / "codex-ai-devkit"
    manifest = plugin / ".codex-plugin" / "plugin.json"
    skill = plugin / "skills" / "ai-devkit-router" / "SKILL.md"
    scripts = plugin / "scripts"
    return {
        "id": "codex",
        "path": str(plugin),
        "manifest_exists": manifest.exists(),
        "skill_exists": skill.exists(),
        "scripts_exists": scripts.is_dir(),
        "status": "ok" if manifest.exists() and skill.exists() and scripts.is_dir() else "error",
    }


def claude_source(root: Path) -> dict[str, Any]:
    plugin = root / "plugins" / "claude-code-ai-devkit"
    manifest = plugin / "plugin.json"
    skill = plugin / "skills" / "ai-devkit-router" / "SKILL.md"
    commands = plugin / "commands"
    scripts = plugin / "scripts"
    return {
        "id": "claude-code",
        "path": str(plugin),
        "manifest_exists": manifest.exists(),
        "skill_exists": skill.exists(),
        "commands_exists": commands.is_dir(),
        "scripts_exists": scripts.is_dir(),
        "status": "ok" if manifest.exists() and skill.exists() and commands.is_dir() and scripts.is_dir() else "error",
    }


def claude_desktop_source(root: Path) -> dict[str, Any]:
    plugin = root / "plugins" / "claude-skill-ai-devkit"
    manifest = plugin / "plugin.json"
    skill = plugin / "ai-devkit" / "SKILL.md"
    references = plugin / "ai-devkit" / "references"
    return {
        "id": "claude-desktop",
        "path": str(plugin),
        "manifest_exists": manifest.exists(),
        "skill_exists": skill.exists(),
        "references_exists": references.is_dir(),
        "status": "ok" if manifest.exists() and skill.exists() and references.is_dir() else "error",
    }


def installed_plugins(base: Path, lock: dict[str, Any]) -> dict[str, Any]:
    declared_hosts = declared_lock_hosts(lock)
    hosts = declared_hosts or ["codex", "claude-code", "claude-desktop"]
    status: dict[str, Any] = {}
    if "codex" in hosts:
        codex_plugin = base / ".codex" / "plugins" / "ai-devkit" / ".codex-plugin" / "plugin.json"
        codex_skill = base / ".codex" / "skills" / "ai-devkit-router" / "SKILL.md"
        status["codex"] = {
            "plugin_exists": codex_plugin.exists(),
            "skill_exists": codex_skill.exists(),
            "status": "ok" if codex_plugin.exists() and codex_skill.exists() else "missing",
        }
    if "claude-code" in hosts:
        claude_plugin = base / ".claude" / "plugins" / "ai-devkit" / "plugin.json"
        claude_skill = base / ".claude" / "skills" / "ai-devkit-router" / "SKILL.md"
        claude_commands = base / ".claude" / "commands"
        status["claude-code"] = {
            "plugin_exists": claude_plugin.exists(),
            "skill_exists": claude_skill.exists(),
            "commands_exists": claude_commands.is_dir(),
            "status": "ok" if claude_plugin.exists() and claude_skill.exists() and claude_commands.is_dir() else "missing",
        }
    if "claude-desktop" in hosts:
        claude_desktop_plugin = base / ".claude" / "plugins" / "ai-devkit-skill" / "plugin.json"
        claude_desktop_skill = base / ".claude" / "skills" / "ai-devkit" / "SKILL.md"
        claude_desktop_refs = base / ".claude" / "skills" / "ai-devkit" / "references"
        status["claude-desktop"] = {
            "plugin_exists": claude_desktop_plugin.exists(),
            "skill_exists": claude_desktop_skill.exists(),
            "references_exists": claude_desktop_refs.is_dir(),
            "status": "ok" if claude_desktop_plugin.exists() and claude_desktop_skill.exists() and claude_desktop_refs.is_dir() else "missing",
        }
    return status


def declared_lock_hosts(lock: dict[str, Any]) -> list[str]:
    install = lock.get("install") if isinstance(lock, dict) else {}
    hosts = install.get("hosts") if isinstance(install, dict) else []
    return [str(item) for item in hosts] if isinstance(hosts, list) else []


def any_host_declared(lock: dict[str, Any]) -> bool:
    return bool(lock.get("exists") and declared_lock_hosts(lock))


def count_status(items: list[dict[str, Any]], status: str) -> int:
    return sum(1 for item in items if item.get("status") == status)
