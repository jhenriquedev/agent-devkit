"""Project-local team profile support."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from cli.aikit.errors import DevKitError


TEAM_SCHEMA_VERSION = "agent-devkit.team/v1"
TEAM_DIR = ".agent-devkit"
TEAM_FILE = "team.yaml"
SECRET_KEY_PATTERN = re.compile(r"(token|secret|password|api[_-]?key|pat|credential)", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(r"(sk-[A-Za-z0-9]|ghp_[A-Za-z0-9]|xox[baprs]-|-----BEGIN [A-Z ]*PRIVATE KEY-----)")


def team_init(project: Path | None = None, *, force: bool = False) -> dict[str, Any]:
    path = team_profile_path(project)
    if path.exists() and not force:
        return team_status(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = default_team_payload()
    write_team_payload(path, payload)
    return {
        "kind": "team",
        "schema_version": TEAM_SCHEMA_VERSION,
        "status": "initialized",
        "path": str(path),
        "profile": payload["active_profile"],
        "secret_free": True,
    }


def team_status(project: Path | None = None) -> dict[str, Any]:
    path = team_profile_path(project)
    if not path.exists():
        return {
            "kind": "team",
            "schema_version": TEAM_SCHEMA_VERSION,
            "status": "not-configured",
            "path": str(path),
            "active_profile": None,
            "profiles": [],
            "next_steps": ["Run `agent team init` to create a project-local team profile."],
        }
    payload = read_team_payload(path)
    findings = secret_findings(payload)
    profiles = payload.get("profiles") if isinstance(payload.get("profiles"), dict) else {}
    active_profile = str(payload.get("active_profile") or "")
    return {
        "kind": "team",
        "schema_version": TEAM_SCHEMA_VERSION,
        "status": "ok" if active_profile in profiles and not findings else "blocked",
        "path": str(path),
        "active_profile": active_profile,
        "profiles": sorted(profiles),
        "secret_free": not findings,
        "findings": findings,
    }


def team_doctor(project: Path | None = None) -> dict[str, Any]:
    status = team_status(project)
    checks = [
        {"id": "team-file-exists", "status": "passed" if status["status"] != "not-configured" else "failed"},
        {"id": "active-profile-exists", "status": "passed" if status.get("active_profile") in set(status.get("profiles") or []) else "failed"},
        {"id": "no-secret-material", "status": "passed" if status.get("secret_free") is not False else "failed"},
    ]
    return {
        "kind": "team-doctor",
        "schema_version": TEAM_SCHEMA_VERSION,
        "status": "ok" if all(check["status"] == "passed" for check in checks) else "blocked",
        "team": status,
        "checks": checks,
    }


def team_onboard(project: Path | None = None) -> dict[str, Any]:
    status = team_status(project)
    if status["status"] == "not-configured":
        return {
            "kind": "team-onboarding",
            "schema_version": TEAM_SCHEMA_VERSION,
            "status": "needs-init",
            "team": status,
            "next_steps": ["Run `agent team init`.", "Review `.agent-devkit/team.yaml` before committing it."],
        }
    return {
        "kind": "team-onboarding",
        "schema_version": TEAM_SCHEMA_VERSION,
        "status": "ok" if status["status"] == "ok" else "blocked",
        "team": status,
        "next_steps": [
            "Configure personal secret refs locally with `agent secret set ... --env ...`.",
            "Run `agent doctor --project .` to validate personal and project setup.",
            "Install desired team workflows locally with `agent workflow install <id> --dry-run` first.",
        ],
    }


def team_profile_list(project: Path | None = None) -> dict[str, Any]:
    payload = require_team_payload(project)
    profiles = payload.get("profiles") if isinstance(payload.get("profiles"), dict) else {}
    return {
        "kind": "team-profiles",
        "schema_version": TEAM_SCHEMA_VERSION,
        "status": "ok",
        "active_profile": payload.get("active_profile"),
        "items": [public_profile(profile_id, profile) for profile_id, profile in sorted(profiles.items())],
    }


def team_profile_show(profile_id: str | None, project: Path | None = None) -> dict[str, Any]:
    payload = require_team_payload(project)
    profile_id = profile_id or str(payload.get("active_profile") or "")
    profile = require_profile(payload, profile_id)
    return {
        "kind": "team-profile",
        "schema_version": TEAM_SCHEMA_VERSION,
        "status": "ok",
        "active": profile_id == payload.get("active_profile"),
        "profile": public_profile(profile_id, profile, detailed=True),
    }


def team_profile_use(profile_id: str | None, project: Path | None = None) -> dict[str, Any]:
    if not profile_id:
        raise DevKitError("team profile use requires a profile id")
    path = team_profile_path(project)
    payload = require_team_payload(project)
    require_profile(payload, profile_id)
    payload["active_profile"] = profile_id
    write_team_payload(path, payload)
    return team_profile_show(profile_id, project)


def team_profile_export(profile_id: str | None, destination: str | None, project: Path | None = None) -> dict[str, Any]:
    payload = require_team_payload(project)
    profile_id = profile_id or str(payload.get("active_profile") or "")
    profile = require_profile(payload, profile_id)
    export_payload = {"schema_version": TEAM_SCHEMA_VERSION, "profile_id": profile_id, "profile": profile}
    findings = secret_findings(export_payload)
    if findings:
        raise DevKitError("team profile export blocked because profile contains secret-like material")
    if not destination:
        return {
            "kind": "team-profile-export",
            "schema_version": TEAM_SCHEMA_VERSION,
            "status": "planned",
            "profile_id": profile_id,
            "payload": export_payload,
            "writes": [],
        }
    target = Path(destination).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    write_team_payload(target, export_payload)
    return {
        "kind": "team-profile-export",
        "schema_version": TEAM_SCHEMA_VERSION,
        "status": "exported",
        "profile_id": profile_id,
        "path": str(target),
        "writes": [str(target)],
    }


def team_profile_import(source: str | None, project: Path | None = None) -> dict[str, Any]:
    if not source:
        raise DevKitError("team profile import requires a path")
    source_path = Path(source).expanduser().resolve()
    if not source_path.exists():
        raise DevKitError(f"team profile import path not found: {source_path}")
    imported = read_team_payload(source_path)
    findings = secret_findings(imported)
    if findings:
        return {
            "kind": "team-profile-import",
            "schema_version": TEAM_SCHEMA_VERSION,
            "status": "blocked",
            "path": str(source_path),
            "findings": findings,
        }
    profile_id = str(imported.get("profile_id") or imported.get("id") or source_path.stem)
    profile = imported.get("profile") if isinstance(imported.get("profile"), dict) else imported
    path = team_profile_path(project)
    payload = default_team_payload() if not path.exists() else read_team_payload(path)
    profiles = payload.setdefault("profiles", {})
    if not isinstance(profiles, dict):
        raise DevKitError("team profile registry is invalid")
    profiles[profile_id] = profile
    write_team_payload(path, payload)
    return {
        "kind": "team-profile-import",
        "schema_version": TEAM_SCHEMA_VERSION,
        "status": "imported",
        "profile_id": profile_id,
        "path": str(path),
    }


def team_profile_path(project: Path | None = None) -> Path:
    root = (project or Path.cwd()).resolve()
    return root / TEAM_DIR / TEAM_FILE


def default_team_payload() -> dict[str, Any]:
    return {
        "schema_version": TEAM_SCHEMA_VERSION,
        "active_profile": "default",
        "profiles": {
            "default": {
                "description": "Default project team profile",
                "providers": [],
                "sources": [],
                "workflows": ["daily-pr-review"],
                "permissions": {"default_mode": "report-only", "external_writes": "confirm"},
                "local_llm": {"enabled": "personal", "max_context_chars": 6000},
                "prompt_injection": {"external_content_policy": "quote-as-data"},
                "secret_refs": [],
            }
        },
    }


def require_team_payload(project: Path | None = None) -> dict[str, Any]:
    path = team_profile_path(project)
    if not path.exists():
        raise DevKitError("team profile not configured. Run `agent team init` first.")
    return read_team_payload(path)


def require_profile(payload: dict[str, Any], profile_id: str) -> dict[str, Any]:
    profiles = payload.get("profiles") if isinstance(payload.get("profiles"), dict) else {}
    profile = profiles.get(profile_id)
    if not isinstance(profile, dict):
        raise DevKitError(f"team profile not found: {profile_id}")
    return profile


def public_profile(profile_id: str, profile: dict[str, Any], *, detailed: bool = False) -> dict[str, Any]:
    item = {
        "id": profile_id,
        "description": profile.get("description"),
        "providers": list_value(profile.get("providers")),
        "sources": list_value(profile.get("sources")),
        "workflows": list_value(profile.get("workflows")),
        "secret_refs_count": len(list_value(profile.get("secret_refs"))),
    }
    if detailed:
        item["permissions"] = profile.get("permissions") if isinstance(profile.get("permissions"), dict) else {}
        item["local_llm"] = profile.get("local_llm") if isinstance(profile.get("local_llm"), dict) else {}
        item["prompt_injection"] = profile.get("prompt_injection") if isinstance(profile.get("prompt_injection"), dict) else {}
    return item


def list_value(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def read_team_payload(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        payload = yaml.safe_load(text) or {}
    except ImportError:
        payload = read_simple_team_yaml(text)
    if not isinstance(payload, dict):
        raise DevKitError(f"team profile file is invalid: {path}")
    return payload


def write_team_payload(path: Path, payload: dict[str, Any]) -> None:
    try:
        import yaml  # type: ignore

        text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    except ImportError:
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")


def read_simple_team_yaml(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        return {}
    if stripped.startswith("{"):
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    lines = [
        (len(raw_line) - len(raw_line.lstrip(" ")), raw_line.strip())
        for raw_line in text.splitlines()
        if raw_line.strip() and not raw_line.lstrip().startswith("#")
    ]
    data, index = parse_simple_yaml_block(lines, 0, 0)
    if index < len(lines):
        raise DevKitError("team profile YAML fallback parser could not read the complete file")
    return data if isinstance(data, dict) else {}


def parse_simple_yaml_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index < len(lines) and lines[index][0] == indent and lines[index][1].startswith("- "):
        values: list[Any] = []
        while index < len(lines) and lines[index][0] == indent and lines[index][1].startswith("- "):
            values.append(parse_simple_scalar(lines[index][1][2:].strip()))
            index += 1
        return values, index

    data: dict[str, Any] = {}
    while index < len(lines):
        line_indent, content = lines[index]
        if line_indent < indent or content.startswith("- "):
            break
        if line_indent > indent:
            raise DevKitError("team profile YAML fallback parser found unexpected indentation")
        if ":" not in content:
            raise DevKitError("team profile YAML fallback parser found an unsupported line")
        key, raw_value = content.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        index += 1
        if raw_value:
            data[key] = parse_simple_scalar(raw_value)
            continue
        if index >= len(lines) or lines[index][0] < indent:
            data[key] = {}
            continue
        if lines[index][0] == indent and lines[index][1].startswith("- "):
            data[key], index = parse_simple_yaml_block(lines, index, indent)
            continue
        if lines[index][0] <= indent:
            data[key] = {}
            continue
        data[key], index = parse_simple_yaml_block(lines, index, lines[index][0])
    return data, index


def parse_simple_scalar(value: str) -> Any:
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if value in {"true", "false"}:
        return value == "true"
    if value.isdigit():
        return int(value)
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value.strip('"')
    if value.startswith("'") and value.endswith("'"):
        return value.strip("'")
    return value


def secret_findings(value: Any, *, path: str = "") -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{path}.{key}" if path else str(key)
            if SECRET_KEY_PATTERN.search(str(key)) and not is_reference_key(str(key)) and item not in (None, "", [], {}):
                findings.append({"path": key_path, "reason": "secret-like-key"})
            findings.extend(secret_findings(item, path=key_path))
        return findings
    if isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(secret_findings(item, path=f"{path}[{index}]"))
        return findings
    if isinstance(value, str) and SECRET_VALUE_PATTERN.search(value):
        findings.append({"path": path, "reason": "secret-like-value"})
    return findings


def is_reference_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in {"secret_ref", "secret_refs", "credential_ref", "credential_refs"} or normalized.endswith("_ref") or normalized.endswith("_refs")
