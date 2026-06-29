"""Local user-created skills, scripts and agent scaffolds."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.aikit.app_home import app_home, ensure_app_home
from cli.aikit.errors import DevKitError


LOCAL_ARTIFACT_SCHEMA_VERSION = "agent-devkit.local-artifacts/v1"
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def skill_create(skill_id: str | None, *, description: str | None = None, force: bool = False) -> dict[str, Any]:
    item_id = require_id(skill_id, "skill id")
    path = local_home("skills") / item_id
    if path.exists() and not force:
        raise DevKitError(f"local skill already exists: {item_id}")
    path.mkdir(parents=True, exist_ok=True)
    skill_path = path / "SKILL.md"
    if force or not skill_path.exists():
        skill_path.write_text(render_skill(item_id, description), encoding="utf-8")
    return local_artifact_payload("local-skill", "created", item_id, path, write_policy="local_config_write")


def skill_list() -> dict[str, Any]:
    return local_artifact_list("local-skills", "skills", marker="SKILL.md")


def skill_show(skill_id: str | None) -> dict[str, Any]:
    return local_artifact_show("local-skill", "skills", require_id(skill_id, "skill id"), marker="SKILL.md")


def skill_update(skill_id: str | None, *, description: str | None = None) -> dict[str, Any]:
    item_id = require_id(skill_id, "skill id")
    path = local_home("skills") / item_id
    if not path.exists():
        raise DevKitError(f"local skill not found: {item_id}")
    (path / "SKILL.md").write_text(render_skill(item_id, description), encoding="utf-8")
    return local_artifact_payload("local-skill", "updated", item_id, path, write_policy="local_config_write")


def skill_delete(skill_id: str | None, *, yes: bool = False) -> dict[str, Any]:
    item_id = require_id(skill_id, "skill id")
    path = local_home("skills") / item_id
    if not yes:
        payload = local_artifact_payload("local-skill", "needs-confirmation", item_id, path, write_policy="local_config_write")
        payload["ok"] = False
        payload["exit_code"] = 2
        return payload
    shutil.rmtree(path, ignore_errors=True)
    return local_artifact_payload("local-skill", "deleted", item_id, path, write_policy="local_config_write")


def script_create(script_id: str | None, *, command: str | None = None, force: bool = False) -> dict[str, Any]:
    item_id = require_id(script_id, "script id")
    path = local_home("scripts") / f"{item_id}.sh"
    if path.exists() and not force:
        raise DevKitError(f"local script already exists: {item_id}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_script(command), encoding="utf-8")
    path.chmod(0o755)
    return local_artifact_payload("local-script", "created", item_id, path, write_policy="local_write")


def script_list() -> dict[str, Any]:
    home = local_home("scripts")
    items = [
        local_artifact_item(path.stem, path, "local-script", enabled=True)
        for path in sorted(home.glob("*.sh"))
    ]
    return {"kind": "local-scripts", "schema_version": LOCAL_ARTIFACT_SCHEMA_VERSION, "status": "ok", "home": str(home), "items": items}


def script_run(script_id: str | None, *, dry_run: bool = False, yes: bool = False) -> dict[str, Any]:
    item_id = require_id(script_id, "script id")
    path = local_home("scripts") / f"{item_id}.sh"
    if not path.exists():
        raise DevKitError(f"local script not found: {item_id}")
    if dry_run or not yes:
        return {
            "kind": "local-script-run",
            "schema_version": LOCAL_ARTIFACT_SCHEMA_VERSION,
            "status": "planned" if dry_run else "needs-confirmation",
            "ok": bool(dry_run),
            "id": item_id,
            "path": str(path),
            "command": [str(path)],
            "write_policy": "local_write",
            "message": "Use --yes to run the local script." if not dry_run and not yes else "Dry-run only.",
            **({} if dry_run else {"exit_code": 2}),
        }
    process = subprocess.run([str(path)], check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
    return {
        "kind": "local-script-run",
        "schema_version": LOCAL_ARTIFACT_SCHEMA_VERSION,
        "status": "ok" if process.returncode == 0 else "failed",
        "ok": process.returncode == 0,
        "id": item_id,
        "path": str(path),
        "exit_code": process.returncode,
        "stdout": process.stdout[-4000:],
        "stderr": process.stderr[-4000:],
        "write_policy": "local_write",
    }


def local_agent_create(agent_id: str | None, *, description: str | None = None, force: bool = False) -> dict[str, Any]:
    item_id = require_id(agent_id, "agent id")
    path = local_home("agents") / item_id
    if path.exists() and not force:
        raise DevKitError(f"local agent already exists: {item_id}")
    (path / "capabilities").mkdir(parents=True, exist_ok=True)
    (path / "knowledge").mkdir(parents=True, exist_ok=True)
    (path / "templates").mkdir(parents=True, exist_ok=True)
    (path / "infra").mkdir(parents=True, exist_ok=True)
    (path / "agent.yaml").write_text(render_agent_yaml(item_id, description), encoding="utf-8")
    (path / "README.md").write_text(f"# {item_id}\n\n{description or 'Local Agent DevKit agent.'}\n", encoding="utf-8")
    return local_artifact_payload("local-agent", "created", item_id, path, write_policy="local_config_write")


def local_agent_validate(agent_id: str | None) -> dict[str, Any]:
    item_id = require_id(agent_id, "agent id")
    path = local_home("agents") / item_id
    checks = [
        {"id": "path-exists", "status": "passed" if path.exists() else "failed"},
        {"id": "agent-yaml", "status": "passed" if (path / "agent.yaml").exists() else "failed"},
        {"id": "capabilities-dir", "status": "passed" if (path / "capabilities").is_dir() else "failed"},
        {"id": "knowledge-dir", "status": "passed" if (path / "knowledge").is_dir() else "failed"},
    ]
    return {
        "kind": "local-agent-validation",
        "schema_version": LOCAL_ARTIFACT_SCHEMA_VERSION,
        "status": "passed" if all(check["status"] == "passed" for check in checks) else "failed",
        "id": item_id,
        "path": str(path),
        "checks": checks,
    }


def local_agent_show(agent_id: str | None) -> dict[str, Any]:
    item_id = require_id(agent_id, "agent id")
    path = local_home("agents") / item_id
    if not (path / "agent.yaml").exists():
        raise DevKitError(f"local agent not found: {item_id}")
    payload = local_artifact_payload("local-agent", "ok", item_id, path, write_policy="read_only")
    payload["manifest"] = (path / "agent.yaml").read_text(encoding="utf-8")
    readme = path / "README.md"
    if readme.exists():
        payload["readme"] = readme.read_text(encoding="utf-8")
    return payload


def local_agent_list() -> dict[str, Any]:
    return local_artifact_list("local-agents", "agents", marker="agent.yaml")


def local_automation_create(
    automation_id: str | None,
    *,
    title: str | None = None,
    prompt: str | None = None,
    command: str | None = None,
    every: str | None = None,
    cron: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    item_id = generated_id(automation_id, title, prefix="automation")
    path = local_home("automations") / item_id
    manifest = path / "automation.json"
    if manifest.exists() and not force:
        raise DevKitError(f"local automation already exists: {item_id}")
    path.mkdir(parents=True, exist_ok=True)
    payload = automation_manifest(item_id, title=title, prompt=prompt, command=command, every=every, cron=cron, enabled=True)
    write_json(manifest, payload)
    if command:
        script_path = path / "run.sh"
        script_path.write_text(render_script(command), encoding="utf-8")
        script_path.chmod(0o755)
    return local_automation_payload("created", item_id, path, payload)


def local_automation_list() -> dict[str, Any]:
    home = local_home("automations")
    items = []
    for manifest in sorted(home.glob("*/automation.json")):
        payload = read_json(manifest)
        item_id = str(payload.get("id") or manifest.parent.name)
        items.append(
            {
                "id": item_id,
                "kind": "local-automation",
                "path": str(manifest.parent),
                "enabled": payload.get("enabled") is True,
                "title": payload.get("title"),
                "schedule": payload.get("schedule") or {},
                "write_policy": payload.get("write_policy") or "local_write",
            }
        )
    return {"kind": "local-automations", "schema_version": LOCAL_ARTIFACT_SCHEMA_VERSION, "status": "ok", "home": str(home), "items": items}


def local_automation_show(automation_id: str | None) -> dict[str, Any]:
    item_id = require_id(automation_id, "automation id")
    path = local_home("automations") / item_id
    payload = read_required_automation(path, item_id)
    return local_automation_payload("ok", item_id, path, payload)


def local_automation_update(
    automation_id: str | None,
    *,
    title: str | None = None,
    prompt: str | None = None,
    command: str | None = None,
    every: str | None = None,
    cron: str | None = None,
) -> dict[str, Any]:
    item_id = require_id(automation_id, "automation id")
    path = local_home("automations") / item_id
    current = read_required_automation(path, item_id)
    current_schedule = current.get("schedule") if isinstance(current.get("schedule"), dict) else {"type": "manual"}
    updated = automation_manifest(
        item_id,
        title=title if title is not None else str(current.get("title") or ""),
        prompt=prompt if prompt is not None else current.get("prompt"),
        command=command if command is not None else current.get("command"),
        every=every,
        cron=cron,
        enabled=current.get("enabled") is not False,
        created_at=str(current.get("created_at") or now_iso()),
    )
    if every is None and cron is None:
        updated["schedule"] = current_schedule
    write_json(path / "automation.json", updated)
    return local_automation_payload("updated", item_id, path, updated)


def local_automation_enable(automation_id: str | None, enabled: bool) -> dict[str, Any]:
    item_id = require_id(automation_id, "automation id")
    path = local_home("automations") / item_id
    payload = read_required_automation(path, item_id)
    payload["enabled"] = enabled
    payload["updated_at"] = now_iso()
    write_json(path / "automation.json", payload)
    return local_automation_payload("enabled" if enabled else "disabled", item_id, path, payload)


def local_automation_remove(automation_id: str | None, *, yes: bool = False) -> dict[str, Any]:
    item_id = require_id(automation_id, "automation id")
    path = local_home("automations") / item_id
    if not yes:
        payload = local_artifact_payload("local-automation", "needs-confirmation", item_id, path, write_policy="local_config_write")
        payload["ok"] = False
        payload["exit_code"] = 2
        return payload
    shutil.rmtree(path, ignore_errors=True)
    return local_artifact_payload("local-automation", "removed", item_id, path, write_policy="local_config_write")


def local_automation_validate(automation_id: str | None) -> dict[str, Any]:
    item_id = require_id(automation_id, "automation id")
    path = local_home("automations") / item_id
    payload = read_json(path / "automation.json") if (path / "automation.json").exists() else {}
    checks = [
        {"id": "path-exists", "status": "passed" if path.exists() else "failed"},
        {"id": "manifest-exists", "status": "passed" if (path / "automation.json").exists() else "failed"},
        {"id": "has-action", "status": "passed" if payload.get("prompt") or payload.get("command") else "failed"},
        {"id": "no-stored-secret", "status": "passed" if not contains_secret_like_text(json.dumps(payload, ensure_ascii=False)) else "failed"},
    ]
    return {
        "kind": "local-automation-validation",
        "schema_version": LOCAL_ARTIFACT_SCHEMA_VERSION,
        "status": "passed" if all(check["status"] == "passed" for check in checks) else "failed",
        "id": item_id,
        "path": str(path),
        "checks": checks,
    }


def local_home(*parts: str) -> Path:
    ensure_app_home()
    path = app_home() / "local" / Path(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def local_artifact_list(kind: str, folder: str, *, marker: str) -> dict[str, Any]:
    home = local_home(folder)
    items = [
        local_artifact_item(path.parent.name, path.parent, kind.removesuffix("s"), enabled=True)
        for path in sorted(home.glob(f"*/{marker}"))
    ]
    return {"kind": kind, "schema_version": LOCAL_ARTIFACT_SCHEMA_VERSION, "status": "ok", "home": str(home), "items": items}


def local_artifact_show(kind: str, folder: str, item_id: str, *, marker: str) -> dict[str, Any]:
    path = local_home(folder) / item_id
    marker_path = path / marker
    if not marker_path.exists():
        raise DevKitError(f"{kind} not found: {item_id}")
    payload = local_artifact_payload(kind, "ok", item_id, path, write_policy="read_only")
    payload["content"] = marker_path.read_text(encoding="utf-8")
    return payload


def local_artifact_payload(kind: str, status: str, item_id: str, path: Path, *, write_policy: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "schema_version": LOCAL_ARTIFACT_SCHEMA_VERSION,
        "status": status,
        "id": item_id,
        "path": str(path),
        "write_policy": write_policy,
        "stored_secret": False,
    }


def local_artifact_item(item_id: str, path: Path, kind: str, *, enabled: bool) -> dict[str, Any]:
    return {"id": item_id, "kind": kind, "path": str(path), "enabled": enabled}


def require_id(value: str | None, label: str) -> str:
    item_id = (value or "").strip()
    if not ID_PATTERN.fullmatch(item_id):
        raise DevKitError(f"{label} must use lowercase letters, numbers, dots, dashes or underscores")
    return item_id


def generated_id(value: str | None, title: str | None, *, prefix: str) -> str:
    if value:
        return require_id(value, f"{prefix} id")
    raw = title or f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    slug = re.sub(r"[^a-z0-9._-]+", "-", raw.strip().lower()).strip("-._")
    return require_id(slug or prefix, f"{prefix} id")


def automation_manifest(
    item_id: str,
    *,
    title: str | None,
    prompt: Any,
    command: Any,
    every: str | None,
    cron: str | None,
    enabled: bool,
    created_at: str | None = None,
) -> dict[str, Any]:
    schedule: dict[str, Any] = {"type": "manual"}
    if every:
        schedule = {"type": "interval", "every": every}
    if cron:
        schedule = {"type": "cron", "cron": cron}
    now = now_iso()
    return {
        "schema_version": LOCAL_ARTIFACT_SCHEMA_VERSION,
        "id": item_id,
        "kind": "local-automation",
        "title": title or item_id,
        "prompt": prompt,
        "command": command,
        "schedule": schedule,
        "enabled": enabled,
        "write_policy": "local_write" if command else "local_config_write",
        "external_writes": False,
        "stored_secret": False,
        "created_at": created_at or now,
        "updated_at": now,
    }


def local_automation_payload(status: str, item_id: str, path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    payload = local_artifact_payload("local-automation", status, item_id, path, write_policy=str(manifest.get("write_policy") or "local_config_write"))
    payload["automation"] = manifest
    return payload


def read_required_automation(path: Path, item_id: str) -> dict[str, Any]:
    manifest = path / "automation.json"
    if not manifest.exists():
        raise DevKitError(f"local automation not found: {item_id}")
    return read_json(manifest)


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def contains_secret_like_text(text: str) -> bool:
    return bool(re.search(r"(?i)(api[_-]?key|token|secret|password|senha|pat)\s*[:=]", text))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def render_skill(skill_id: str, description: str | None) -> str:
    return f"""---
name: {skill_id}
description: {description or 'Local Agent DevKit skill.'}
---

# {skill_id}

{description or 'Local skill created by Agent DevKit.'}
"""


def render_script(command: str | None) -> str:
    body = command or "echo 'local script placeholder'"
    return f"#!/usr/bin/env sh\nset -eu\n{body}\n"


def render_agent_yaml(agent_id: str, description: str | None) -> str:
    return json.dumps(
        {
            "id": agent_id,
            "kind": "agent",
            "name": agent_id,
            "version": "0.1.0",
            "status": "draft",
            "purpose": description or "Local Agent DevKit agent.",
            "default_context": ["knowledge/context.md"],
            "capabilities": [],
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"
