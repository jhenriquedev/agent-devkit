"""Local command aliases for the canonical agent CLI."""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path
from typing import Any

from cli.aikit.app_home import app_home, ensure_app_home


ALIAS_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{1,63}$")
RESERVED_ALIASES = {"agent", "aikit", "ai-devkit", "python", "python3"}
SHELL_BLOCK_BEGIN = "# >>> agent-devkit aliases >>>"
SHELL_BLOCK_END = "# <<< agent-devkit aliases <<<"


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


def ensure_alias_for_agent_name(agent_name: str, *, force: bool = False) -> dict[str, Any]:
    suggested = suggest_alias_name(agent_name)
    payload: dict[str, Any] = {
        "kind": "alias",
        "requested_name": agent_name,
        "suggested_name": suggested,
        "created": False,
    }
    if not suggested:
        return {
            **payload,
            "status": "invalid",
            "message": "Agent name cannot be converted to a safe command alias.",
            "path_status": alias_path_status(),
        }
    try:
        added = add_alias(suggested, force=force)
    except ValueError as exc:
        return {
            **payload,
            "name": suggested,
            "status": "blocked",
            "message": str(exc),
            "path_status": alias_path_status(suggested),
        }
    added["created"] = True
    added["requested_name"] = agent_name
    added["suggested_name"] = suggested
    added["path_status"] = alias_path_status(suggested)
    return added


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
        "path_status": alias_path_status(alias),
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


def suggest_alias_name(agent_name: str) -> str | None:
    cleaned = " ".join(str(agent_name or "").split()).strip()
    if not cleaned:
        return None
    try:
        return validate_alias_name(cleaned)
    except ValueError:
        pass
    ascii_name = unicodedata.normalize("NFKD", cleaned).encode("ascii", "ignore").decode("ascii")
    alias = re.sub(r"[^A-Za-z0-9_-]+", "-", ascii_name).strip("-_")
    if alias and not alias[0].isalpha():
        alias = f"agent-{alias}"
    if len(alias) == 1:
        alias = f"{alias}-agent"
    alias = alias[:64].strip("-_")
    if not alias:
        return None
    try:
        return validate_alias_name(alias)
    except ValueError:
        return None


def alias_path_status(alias: str | None = None) -> dict[str, Any]:
    bin_dir = aliases_bin_dir()
    path_entries = os.environ.get("PATH", "").split(os.pathsep) if os.environ.get("PATH") else []
    bin_dir_in_path = any(paths_equal(Path(entry), bin_dir) for entry in path_entries if entry)
    found = shutil.which(alias) if alias else None
    available = False
    if alias and found:
        try:
            available = Path(found).resolve() in {path.resolve() for path in alias_paths(alias)}
        except OSError:
            available = False
    plan = alias_path_setup_plan()
    return {
        "bin_dir": str(bin_dir),
        "bin_dir_in_path": bin_dir_in_path,
        "alias_available": available,
        "found": found,
        "setup_required": not bin_dir_in_path,
        "setup": plan,
    }


def paths_equal(left: Path, right: Path) -> bool:
    try:
        return left.expanduser().resolve() == right.expanduser().resolve()
    except OSError:
        return left.expanduser() == right.expanduser()


def alias_path_setup_plan() -> dict[str, Any]:
    bin_dir = aliases_bin_dir()
    if os.name == "nt":
        return {
            "platform": "windows",
            "target": "user PATH",
            "command": f'agent alias path --yes',
            "description": f"Add {bin_dir} to the current user's PATH.",
        }
    profile = detect_shell_profile()
    return {
        "platform": "posix",
        "target": str(profile),
        "command": "agent alias path --yes",
        "description": f"Add {bin_dir} to PATH for future shell sessions.",
    }


def setup_alias_path(*, yes: bool = False) -> dict[str, Any]:
    status = alias_path_status()
    payload: dict[str, Any] = {
        "kind": "alias-path",
        "bin_dir": status["bin_dir"],
        "path_status": status,
        "executed": False,
    }
    if not status["setup_required"]:
        return {**payload, "status": "ok", "message": "Agent DevKit alias bin directory is already on PATH."}
    if not yes:
        return {
            **payload,
            "status": "needs-confirmation",
            "message": "Run `agent alias path --yes` to make configured aliases available as shell commands.",
        }
    if os.name == "nt":
        return install_windows_user_path(payload)
    return install_posix_shell_path(payload)


def install_posix_shell_path(payload: dict[str, Any]) -> dict[str, Any]:
    profile = detect_shell_profile()
    bin_dir = aliases_bin_dir()
    profile.parent.mkdir(parents=True, exist_ok=True)
    current = profile.read_text(encoding="utf-8") if profile.exists() else ""
    export_line = f'export PATH="{bin_dir}:$PATH"'
    block = f"\n{SHELL_BLOCK_BEGIN}\n{export_line}\n{SHELL_BLOCK_END}\n"
    if str(bin_dir) not in current:
        profile.write_text(current.rstrip() + block, encoding="utf-8")
    return {
        **payload,
        "status": "updated",
        "executed": True,
        "profile": str(profile),
        "message": "Alias PATH configured for future shell sessions. Restart the terminal or source the profile.",
    }


def install_windows_user_path(payload: dict[str, Any]) -> dict[str, Any]:
    bin_dir = str(aliases_bin_dir())
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            try:
                current, value_type = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current, value_type = "", winreg.REG_EXPAND_SZ
            entries = [entry for entry in str(current).split(os.pathsep) if entry]
            if not any(paths_equal(Path(entry), aliases_bin_dir()) for entry in entries):
                new_value = os.pathsep.join([bin_dir, *entries])
                winreg.SetValueEx(key, "Path", 0, value_type, new_value)
    except OSError as exc:
        return {**payload, "status": "failed", "executed": False, "message": str(exc)}
    return {
        **payload,
        "status": "updated",
        "executed": True,
        "profile": "HKCU\\Environment\\Path",
        "message": "Alias PATH configured for future Windows terminal sessions.",
    }


def detect_shell_profile() -> Path:
    shell = Path(os.environ.get("SHELL", "")).name
    home = Path.home()
    if shell == "zsh":
        return home / ".zshrc"
    if shell == "bash":
        return home / ".bashrc"
    return home / ".profile"
