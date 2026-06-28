"""Local command aliases for the canonical agent CLI."""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

from cli.aikit.app_home import app_home, ensure_app_home


ALIAS_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{1,63}$")
RESERVED_ALIASES = {"agent", "aikit", "ai-devkit", "python", "python3"}


def aliases_config_path() -> Path:
    return app_home() / "config" / "aliases.json"


def aliases_bin_dir() -> Path:
    return app_home() / "bin"


def load_aliases() -> dict[str, Any]:
    path = aliases_config_path()
    if not path.exists():
        return {"version": 1, "aliases": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "aliases": {}}
    if not isinstance(data, dict):
        return {"version": 1, "aliases": {}}
    aliases = data.get("aliases")
    if not isinstance(aliases, dict):
        data["aliases"] = {}
    data.setdefault("version", 1)
    return data


def save_aliases(config: dict[str, Any]) -> Path:
    ensure_app_home()
    path = aliases_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def list_aliases() -> dict[str, Any]:
    ensure_app_home()
    config = load_aliases()
    items = []
    invalid = []
    for name, item in sorted(config.get("aliases", {}).items()):
        if not isinstance(item, dict):
            continue
        try:
            alias = validate_alias_name(name)
        except ValueError:
            invalid.append(name)
            continue
        items.append(alias_payload(alias, item))
    return {"kind": "aliases", "status": "ok", "config_path": str(aliases_config_path()), "items": items, "invalid": invalid}


def add_alias(name: str, *, force: bool = False) -> dict[str, Any]:
    alias = validate_alias_name(name)
    ensure_app_home()
    target = alias_executable_path(alias)
    existing = shutil.which(alias)
    if existing and Path(existing).resolve() != target.resolve() and not force:
        raise ValueError(f"alias command already exists on PATH: {existing}. Use --force to overwrite local alias only.")

    config = load_aliases()
    item = {"name": alias, "created_by": "agent-devkit"}
    config.setdefault("aliases", {})[alias] = item
    write_alias_shims(alias)
    written_path = save_aliases(config)
    payload = alias_payload(alias, item)
    payload.update({"kind": "alias", "status": "added", "config_path": str(written_path)})
    return payload


def remove_alias(name: str) -> dict[str, Any]:
    alias = validate_alias_name(name)
    config = load_aliases()
    removed = bool(config.get("aliases", {}).pop(alias, None))
    removed_paths: list[str] = []
    for path in alias_paths(alias):
        if path.exists():
            path.unlink()
            removed_paths.append(str(path))
    written_path = save_aliases(config)
    return {
        "kind": "alias",
        "status": "removed" if removed or removed_paths else "missing",
        "name": alias,
        "config_path": str(written_path),
        "removed_paths": removed_paths,
    }


def sync_aliases() -> dict[str, Any]:
    ensure_app_home()
    config = load_aliases()
    synced: list[dict[str, Any]] = []
    invalid: list[str] = []
    for alias, item in sorted(config.get("aliases", {}).items()):
        if not isinstance(item, dict):
            continue
        try:
            safe_alias = validate_alias_name(alias)
        except ValueError:
            invalid.append(alias)
            continue
        write_alias_shims(safe_alias)
        synced.append(alias_payload(safe_alias, item))
    save_aliases(config)
    return {"kind": "aliases", "status": "synced", "config_path": str(aliases_config_path()), "items": synced, "invalid": invalid}


def validate_alias_name(name: str, *, allow_reserved: bool = False) -> str:
    alias = name.strip()
    if not ALIAS_PATTERN.fullmatch(alias):
        raise ValueError("alias must start with a letter and contain only letters, numbers, hyphen or underscore")
    if alias.lower() in RESERVED_ALIASES and not allow_reserved:
        raise ValueError(f"alias is reserved: {alias}")
    return alias


def alias_payload(alias: str, item: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": alias,
        "path": str(alias_executable_path(alias)),
        "cmd_path": str(aliases_bin_dir() / f"{alias}.cmd"),
        "ps1_path": str(aliases_bin_dir() / f"{alias}.ps1"),
        "created_by": item.get("created_by"),
    }


def write_alias_shims(alias: str) -> None:
    bin_dir = aliases_bin_dir()
    bin_dir.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[2]
    agent_script = root / "agent"
    python = sys.executable

    posix = alias_executable_path(alias)
    posix.write_text(
        "\n".join(
            [
                "#!/usr/bin/env sh",
                "set -eu",
                f"AI_DEVKIT_INVOKED_AS={json.dumps(alias)} exec {json.dumps(python)} {json.dumps(str(agent_script))} \"$@\"",
                "",
            ]
        ),
        encoding="utf-8",
    )
    posix.chmod(0o755)

    cmd = bin_dir / f"{alias}.cmd"
    cmd.write_text(
        "\r\n".join(
            [
                "@echo off",
                f"set AI_DEVKIT_INVOKED_AS={alias}",
                f'"{python}" "{agent_script}" %*',
                "",
            ]
        ),
        encoding="utf-8",
    )

    ps1 = bin_dir / f"{alias}.ps1"
    ps1.write_text(
        "\n".join(
            [
                f"$env:AI_DEVKIT_INVOKED_AS = {json.dumps(alias)}",
                f"& {json.dumps(python)} {json.dumps(str(agent_script))} @args",
                "",
            ]
        ),
        encoding="utf-8",
    )


def alias_executable_path(alias: str) -> Path:
    return aliases_bin_dir() / alias


def alias_paths(alias: str) -> list[Path]:
    return [alias_executable_path(alias), aliases_bin_dir() / f"{alias}.cmd", aliases_bin_dir() / f"{alias}.ps1"]
