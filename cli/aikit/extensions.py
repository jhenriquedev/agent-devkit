"""Local extension registry for Agent DevKit MVP."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from cli.aikit.app_home import ensure_app_home, app_home
from cli.aikit.errors import DevKitError


EXTENSIONS_SCHEMA_VERSION = "agent-devkit.local-extensions/v1"


def local_extensions_list() -> dict[str, Any]:
    data = load_extensions()
    return {
        "kind": "local-extensions",
        "schema_version": EXTENSIONS_SCHEMA_VERSION,
        "status": "ok",
        "items": public_extensions(data["extensions"]),
        "scopes": extension_scopes(),
    }


def local_extension_add(path: str | None) -> dict[str, Any]:
    if not path:
        raise DevKitError("local add requires --path")
    source = Path(path).expanduser().resolve()
    if not source.exists():
        raise DevKitError(f"local extension path not found: {source}")
    data = load_extensions()
    extension_id = source.name
    if any(item["id"] == extension_id for item in data["extensions"]):
        raise DevKitError(f"local extension already registered: {extension_id}")
    item = {"id": extension_id, "path": str(source), "enabled": True, "scope": "user"}
    data["extensions"].append(item)
    save_extensions(data)
    return {"kind": "local-extension", "status": "added", "item": item}


def local_extension_enable(extension_id: str, enabled: bool) -> dict[str, Any]:
    data = load_extensions()
    item = find_extension(data, extension_id)
    item["enabled"] = enabled
    save_extensions(data)
    return {"kind": "local-extension", "status": "enabled" if enabled else "disabled", "item": item}


def local_extension_remove(extension_id: str) -> dict[str, Any]:
    data = load_extensions()
    before = len(data["extensions"])
    data["extensions"] = [item for item in data["extensions"] if item.get("id") != extension_id]
    save_extensions(data)
    return {"kind": "local-extension-remove", "status": "removed" if len(data["extensions"]) < before else "not-found"}


def local_extension_validate(extension_id: str) -> dict[str, Any]:
    data = load_extensions()
    item = find_extension(data, extension_id)
    path = Path(str(item.get("path") or ""))
    checks = [
        {"id": "path-exists", "status": "passed" if path.exists() else "failed"},
        {"id": "has-known-content", "status": "passed" if has_known_extension_content(path) else "failed"},
    ]
    return {
        "kind": "local-extension-validation",
        "status": "passed" if all(check["status"] == "passed" for check in checks) else "failed",
        "item": item,
        "checks": checks,
    }


def extension_scopes() -> dict[str, str]:
    return {"user": str(app_home() / "local"), "project": str(Path.cwd() / ".agent-devkit")}


def extensions_path() -> Path:
    ensure_app_home()
    path = app_home() / "local" / "extensions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_extensions() -> dict[str, Any]:
    path = extensions_path()
    if not path.exists():
        return {"version": 1, "extensions": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": 1, "extensions": []}
    if not isinstance(data, dict) or not isinstance(data.get("extensions"), list):
        return {"version": 1, "extensions": []}
    return {"version": 1, "extensions": [item for item in data["extensions"] if isinstance(item, dict)]}


def save_extensions(data: dict[str, Any]) -> Path:
    path = extensions_path()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def public_extensions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": item.get("id"),
            "path": item.get("path"),
            "enabled": item.get("enabled") is True,
            "scope": item.get("scope") or "user",
        }
        for item in items
    ]


def find_extension(data: dict[str, Any], extension_id: str) -> dict[str, Any]:
    for item in data["extensions"]:
        if item.get("id") == extension_id:
            return item
    raise DevKitError(f"local extension not found: {extension_id}")


def has_known_extension_content(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_file():
        return path.suffix in {".md", ".yaml", ".yml", ".json", ".py", ".sh"}
    return any((path / name).exists() for name in ("agent.yaml", "capability.yaml", "workflow.yaml", "skill.md", "SKILL.md")) or any(
        path.glob("**/agent.yaml")
    )


def copy_extension_fixture(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
