"""Runtime lock file helpers for AI DevKit installs."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from cli.aikit import __version__


PROJECT_LOCK_NAME = "ai-devkit.lock"
GLOBAL_LOCK_NAME = "runtime.lock"


def lock_path(base: Path, scope: str) -> Path:
    name = GLOBAL_LOCK_NAME if scope == "global" else PROJECT_LOCK_NAME
    return base / ".ai-devkit" / name


def write_lock(
    path: Path,
    root: Path,
    *,
    scope: str,
    hosts: tuple[str, ...],
    profiles: list[str] | None = None,
) -> dict[str, Any]:
    data = build_lock(root, scope=scope, hosts=hosts, profiles=profiles or [])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_lock(data), encoding="utf-8")
    return data


def build_lock(
    root: Path,
    *,
    scope: str,
    hosts: tuple[str, ...],
    profiles: list[str],
) -> dict[str, Any]:
    git = git_metadata(root)
    runtime = {
        "source": "local",
        "repository": git["repository"] or str(root),
        "ref": "local-working-tree",
        "commit": git["commit"] or "unknown",
        "git_ref": git["git_ref"] or "unknown",
        "dirty": git["dirty"],
        "version": __version__,
        "installed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "channel": "local",
    }
    data: dict[str, Any] = {
        "runtime": runtime,
        "install": {
            "scope": scope,
            "hosts": list(hosts),
        },
    }
    if scope == "project":
        data["profiles"] = profiles
        data["providers"] = {"policy": "project-overrides-global"}
    return data


def git_metadata(root: Path) -> dict[str, Any]:
    return {
        "repository": run_git(root, "config", "--get", "remote.origin.url"),
        "commit": run_git(root, "rev-parse", "HEAD"),
        "git_ref": run_git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(run_git(root, "status", "--porcelain")),
    }


def run_git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def render_lock(data: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("runtime:")
    for key in ("source", "repository", "ref", "commit", "git_ref", "dirty", "version", "installed_at", "channel"):
        lines.append(f"  {key}: {yaml_scalar(data['runtime'][key])}")
    lines.append("install:")
    lines.append(f"  scope: {yaml_scalar(data['install']['scope'])}")
    lines.append("  hosts:")
    for host in data["install"]["hosts"]:
        lines.append(f"    - {yaml_scalar(host)}")
    if "profiles" in data:
        lines.append("profiles:")
        for profile in data["profiles"]:
            lines.append(f"  - {yaml_scalar(profile)}")
    if "providers" in data:
        lines.append("providers:")
        lines.append(f"  policy: {yaml_scalar(data['providers']['policy'])}")
    lines.append("")
    return "\n".join(lines)


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    text = str(value)
    if not text or any(char in text for char in ":#{}[],&*?<>=!%@\\\"'") or text.lower() in {"true", "false", "null"}:
        return json.dumps(text)
    return text


def parse_profiles(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def read_lock(path: Path) -> dict[str, Any]:
    payload = {
        "path": str(path),
        "exists": path.exists(),
        "runtime": {},
    }
    if not path.exists():
        return payload
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        data = read_simple_lock(path)
    if not isinstance(data, dict):
        data = {}
    runtime = data.get("runtime") if isinstance(data.get("runtime"), dict) else {}
    payload["runtime"] = runtime
    payload["install"] = data.get("install", {}) if isinstance(data.get("install"), dict) else {}
    payload["profiles"] = data.get("profiles", []) if isinstance(data.get("profiles"), list) else []
    return payload


def read_simple_lock(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current: dict[str, Any] | None = None
    current_list: list[str] | None = None
    nested_list_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" ") and raw_line.endswith(":"):
            key = raw_line[:-1].strip()
            if key in {"profiles"}:
                current_list = []
                data[key] = current_list
                current = None
            else:
                current = {}
                current_list = None
                nested_list_key = None
                data[key] = current
            continue
        stripped = raw_line.strip()
        if current_list is not None and stripped.startswith("- "):
            current_list.append(parse_scalar(stripped[2:]))
            continue
        if current is not None and nested_list_key and stripped.startswith("- "):
            nested = current.setdefault(nested_list_key, [])
            if isinstance(nested, list):
                nested.append(parse_scalar(stripped[2:]))
            continue
        if current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                current[key] = parse_scalar(value)
                nested_list_key = None
            else:
                current[key] = []
                nested_list_key = key
    return data


def parse_scalar(value: str) -> Any:
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value.strip('"')
    return value


def compare_locks(global_lock: dict[str, Any], project_lock: dict[str, Any]) -> dict[str, Any]:
    if not global_lock["exists"] and not project_lock["exists"]:
        return {"status": "missing", "global": global_lock, "project": project_lock, "differences": []}
    if global_lock["exists"] and not project_lock["exists"]:
        return {"status": "global-only", "global": global_lock, "project": project_lock, "differences": []}
    if project_lock["exists"] and not global_lock["exists"]:
        return {"status": "project-only", "global": global_lock, "project": project_lock, "differences": []}

    differences = []
    for key in ("source", "repository", "ref", "commit", "version"):
        global_value = (global_lock.get("runtime") or {}).get(key)
        project_value = (project_lock.get("runtime") or {}).get(key)
        if global_value != project_value:
            differences.append({"field": key, "global": global_value, "project": project_value})
    return {
        "status": "diverged" if differences else "ok",
        "global": global_lock,
        "project": project_lock,
        "differences": differences,
    }


def lock_status(project: Path | None, home: Path | None = None) -> dict[str, Any]:
    global_base = (home or Path(os.environ.get("AIKIT_INSTALL_HOME", str(Path.home())))).expanduser().resolve()
    global_lock = read_lock(lock_path(global_base, "global"))
    project_lock = read_lock(lock_path(project.resolve(), "project")) if project else {"exists": False, "runtime": {}}
    return compare_locks(global_lock, project_lock)
