"""Local AI DevKit memory and napkin helpers."""

from __future__ import annotations

import re
import shutil
import hashlib
import hmac
import base64
import io
import json
import os
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.aikit.app_home import (
    app_path,
    cache_home,
    ensure_app_home,
    memory_home as app_memory_home,
    sessions_home,
    tasks_home,
)
from cli.aikit.llm import config_path, load_config, save_config


SECRET_VALUE_PATTERN = re.compile(
    r"(?i)\b("
    r"sk-[a-z0-9_-]{12,}|"
    r"npm_[a-z0-9]{12,}|"
    r"gh[pousr]_[a-z0-9_]{12,}|"
    r"xox[baprs]-[a-z0-9-]{12,}|"
    r"AKIA[0-9A-Z]{12,}|"
    r"ASIA[0-9A-Z]{12,}"
    r")\b"
)
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)([\"']?)([a-z0-9_]*(?:token|secret|password|passwd|pwd|senha|chave|api[_-]?key|private[_-]?key)[a-z0-9_]*)([\"']?)(\s*[:=]\s*)([\"']?)([^\s,;}\"']+)([\"']?)"
)

MEMORY_FILE_TEMPLATES: dict[str, str] = {
    "profile.md": """# Profile

Local user profile for Agent DevKit.

## User

- Name:
- Primary language:
- Timezone:

## Notes

- Add stable facts the agent should remember.
""",
    "personality.md": """# Personality

Configured public identity and response style for Agent DevKit.

## Agent

- Name: Agent DevKit

## Style

- Tone: direct
- Detail level: concise
""",
    "preferences.md": """# Preferences

Reusable user preferences.

## Defaults

- Prefer local-first execution.
- Ask before external writes.
""",
    "projects.md": """# Projects

Frequently used projects and repositories.

## Items

- Add project names, paths, and non-secret references here.
""",
    "routines.md": """# Routines

Recurring workflows, checks, and habits.

## Items

- Add routines that should be easy to reuse.
""",
    "napkin.md": """# Agent DevKit Napkin

Curated local runbook entries promoted from repeated use.

## Execution & Validation

- Keep high-value reusable notes here.
""",
}
BACKUP_PACKAGE_SCHEMA_VERSION = "agent-devkit.memory-backup-package/v1"
BACKUP_PACKAGE_ALGORITHM = "PBKDF2-HMAC-SHA256/XOR-HMAC-SHA256"


def memory_home() -> Path:
    return app_memory_home()


def memory_backups_home() -> Path:
    return app_path("backups", "memory")


def ensure_memory() -> dict[str, Any]:
    ensure_app_home()
    home = memory_home()
    home.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, Any]] = []
    created: list[str] = []
    for name, template in MEMORY_FILE_TEMPLATES.items():
        path = home / name
        if not path.exists():
            path.write_text(template, encoding="utf-8")
            created.append(str(path))
        files.append({"name": name, "path": str(path), "exists": path.exists()})
    return {
        "kind": "memory-path",
        "status": "ok",
        "home": str(home),
        "created": created,
        "files": files,
    }


def normalize_prompt(prompt: str) -> str:
    text = " ".join(redact_secrets(prompt).lower().split())
    return text[:160]


def redact_secrets(value: str) -> str:
    redacted = SECRET_VALUE_PATTERN.sub("[REDACTED_SECRET]", value)
    return SECRET_ASSIGNMENT_PATTERN.sub(r"\1\2\3\4\5[REDACTED_SECRET]\7", redacted)


def napkin_context(root: Path, *, agent_id: str | None = None, source_id: str | None = None) -> dict[str, Any]:
    paths = [
        root / "vendor" / "skills" / "napkin" / "napkin.md",
        memory_home() / "napkin.md",
        memory_home() / "global" / "napkin.md",
    ]
    if agent_id:
        paths.append(memory_home() / "agents" / sanitize_segment(agent_id) / "napkin.md")
    if source_id:
        paths.append(memory_home() / "sources" / sanitize_segment(source_id) / "napkin.md")
    return {
        "loaded": any(path.exists() for path in paths),
        "paths": [
            {
                "path": str(path),
                "exists": path.exists(),
            }
            for path in paths
        ],
    }


def record_usage(
    prompt: str,
    *,
    route: dict[str, Any] | None = None,
    source_id: str | None = None,
) -> None:
    config = load_config()
    memory = config.setdefault("memory", {})
    usage = memory.setdefault("usage", {})
    now = datetime.now(timezone.utc).isoformat()
    increment_bucket(usage.setdefault("prompts", {}), normalize_prompt(prompt), now)
    if route:
        route_key = f"{route.get('agent_id')}/{route.get('capability_id')}"
        increment_bucket(usage.setdefault("routes", {}), route_key, now)
    if source_id:
        increment_bucket(usage.setdefault("sources", {}), source_id, now)
    save_config(config)


def show_memory(root: Path, *, agent_id: str | None = None, source_id: str | None = None) -> dict[str, Any]:
    memory_paths = ensure_memory()
    config = load_config()
    memory = config.get("memory") if isinstance(config.get("memory"), dict) else {}
    usage = memory.get("usage") if isinstance(memory.get("usage"), dict) else {}
    return {
        "kind": "memory",
        "status": "ok",
        "config_path": str(config_path()),
        "memory_home": str(memory_home()),
        "files": memory_paths["files"],
        "usage": {
            "prompts": sorted_usage(usage.get("prompts") or {}),
            "routes": sorted_usage(usage.get("routes") or {}),
            "sources": sorted_usage(usage.get("sources") or {}),
        },
        "napkin": napkin_context(root, agent_id=agent_id, source_id=source_id),
    }


def create_memory_backup(
    *,
    title: str | None = None,
    encrypted: bool = False,
    passphrase_env: str | None = None,
) -> dict[str, Any]:
    memory_paths = ensure_memory()
    backups = memory_backups_home()
    backups.mkdir(parents=True, exist_ok=True)
    backup_id = unique_backup_id(title)
    backup_root = backups / backup_id
    backup_root.mkdir(parents=True, exist_ok=False)
    backup_memory = backup_root / ("_memory-staging" if encrypted else "memory")
    shutil.copytree(memory_home(), backup_memory)

    files = backup_file_inventory(backup_memory)
    manifest = {
        "schema_version": "agent-devkit.memory-backup/v1",
        "id": backup_id,
        "title": title or "Memory backup",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_home": str(memory_home()),
        "storage": "local-filesystem",
        "remote_upload": False,
        "encrypted": encrypted,
        "sensitive_local_copy": not encrypted,
        "files": files,
        "package": None,
        "notes": [
            "This is a local backup only; no remote provider upload was executed.",
            "Remote backup must be encrypted before upload and requires explicit opt-in.",
        ],
    }
    if encrypted:
        package_path = backup_root / f"{backup_id}.adkmb"
        passphrase = passphrase_from_env(passphrase_env)
        write_encrypted_backup_package(package_path, backup_memory, manifest, passphrase)
        manifest["package"] = str(package_path)
        manifest["package_name"] = package_path.name
        shutil.rmtree(backup_memory)
    manifest_path = backup_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    next_steps = [
        f"Restore with `agent memory backup restore {backup_id} --yes`.",
        f"Delete with `agent memory backup delete {backup_id} --yes`.",
    ]
    if encrypted:
        next_steps[0] = f"Restore with `agent memory backup restore {backup_id} --passphrase-env {passphrase_env or 'AGENT_DEVKIT_BACKUP_PASSPHRASE'} --yes`."
        next_steps.insert(1, f"Portable package: {manifest['package']}")
    return {
        "kind": "memory-backup",
        "status": "created",
        "backup": public_backup(manifest, backup_root),
        "home": str(backups),
        "memory_home": memory_paths["home"],
        "next_steps": next_steps,
    }


def list_memory_backups() -> dict[str, Any]:
    backups = memory_backups_home()
    items = []
    if backups.exists():
        for manifest_path in sorted(backups.glob("*/manifest.json")):
            manifest = load_backup_manifest(manifest_path)
            if manifest:
                items.append(public_backup(manifest, manifest_path.parent))
    return {
        "kind": "memory-backups",
        "status": "ok",
        "home": str(backups),
        "count": len(items),
        "items": items,
    }


def restore_memory_backup(
    backup_id: str | None,
    *,
    yes: bool = False,
    backup_file: str | None = None,
    passphrase_env: str | None = None,
) -> dict[str, Any]:
    backup_root, manifest = require_memory_backup(backup_id, backup_file=backup_file, passphrase_env=passphrase_env)
    payload = {
        "kind": "memory-backup-restore",
        "backup": public_backup(manifest, backup_root),
        "memory_home": str(memory_home()),
        "requires_confirmation": True,
    }
    if not yes:
        return {
            **payload,
            "status": "planned",
            "executed": False,
            "next_steps": [restore_next_step(manifest, backup_file=backup_file, passphrase_env=passphrase_env)],
        }

    ensure_app_home()
    safety_backup: str | None = None
    with decrypted_memory_source(backup_root, manifest, passphrase_env=passphrase_env) as source_memory:
        if memory_home().exists():
            safety_root = memory_backups_home() / f"pre-restore-{timestamp_id()}"
            safety_root.mkdir(parents=True, exist_ok=False)
            shutil.copytree(memory_home(), safety_root / "memory")
            safety_backup = str(safety_root)
            shutil.rmtree(memory_home())
        shutil.copytree(source_memory, memory_home())
    return {
        **payload,
        "status": "restored",
        "executed": True,
        "safety_backup": safety_backup,
    }


class decrypted_memory_source:
    def __init__(self, backup_root: Path, manifest: dict[str, Any], *, passphrase_env: str | None = None) -> None:
        self.backup_root = backup_root
        self.manifest = manifest
        self.passphrase_env = passphrase_env
        self.temp_dir: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> Path:
        plain = self.backup_root / "memory"
        if plain.exists():
            return plain
        package_path = package_path_from_manifest(self.backup_root, self.manifest)
        if not package_path:
            raise ValueError(f"memory backup has no restorable memory payload: {self.manifest.get('id')}")
        passphrase = passphrase_from_env(self.passphrase_env)
        self.temp_dir = tempfile.TemporaryDirectory(prefix="agent-devkit-memory-restore-")
        target = Path(self.temp_dir.name)
        extract_encrypted_backup_package(package_path, target, passphrase)
        memory = target / "memory"
        if not memory.exists():
            raise ValueError("encrypted memory backup package did not contain memory/")
        return memory

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        if self.temp_dir:
            self.temp_dir.cleanup()


def restore_next_step(manifest: dict[str, Any], *, backup_file: str | None, passphrase_env: str | None) -> str:
    if manifest.get("encrypted"):
        env_name = passphrase_env or "AGENT_DEVKIT_BACKUP_PASSPHRASE"
        if backup_file:
            return f"Re-run with `agent memory backup restore --file {backup_file} --passphrase-env {env_name} --yes` to restore local memory."
        return f"Re-run with `agent memory backup restore {manifest['id']} --passphrase-env {env_name} --yes` to restore local memory."
    if backup_file:
        return f"Re-run with `agent memory backup restore --file {backup_file} --yes` to restore local memory."
    return f"Re-run with `agent memory backup restore {manifest['id']} --yes` to restore local memory."


def delete_memory_backup(backup_id: str | None, *, yes: bool = False) -> dict[str, Any]:
    backup_root, manifest = require_memory_backup(backup_id)
    payload = {
        "kind": "memory-backup-delete",
        "backup": public_backup(manifest, backup_root),
        "requires_confirmation": True,
    }
    if not yes:
        return {
            **payload,
            "status": "planned",
            "executed": False,
            "next_steps": [f"Re-run with `agent memory backup delete {manifest['id']} --yes` to remove this local backup."],
        }
    shutil.rmtree(backup_root)
    return {
        **payload,
        "status": "deleted",
        "executed": True,
    }


def reset_memory(
    *,
    all_memory: bool = False,
    agent_id: str | None = None,
    source_id: str | None = None,
    reset_sessions: bool = False,
    reset_tasks: bool = False,
    reset_cache: bool = False,
) -> dict[str, Any]:
    config = load_config()
    removed_paths: list[str] = []
    scoped_reset = any([agent_id, source_id, reset_sessions, reset_tasks, reset_cache])
    if all_memory or not scoped_reset:
        config.pop("memory", None)
        if memory_home().exists():
            removed_paths.append(str(memory_home()))
            shutil.rmtree(memory_home())
    else:
        memory = config.get("memory") if isinstance(config.get("memory"), dict) else {}
        usage = memory.get("usage") if isinstance(memory.get("usage"), dict) else {}
        if agent_id:
            usage.get("routes", {}).pop(agent_id, None)
            path = memory_home() / "agents" / sanitize_segment(agent_id)
            remove_path(path, removed_paths)
        if source_id:
            usage.get("sources", {}).pop(source_id, None)
            path = memory_home() / "sources" / sanitize_segment(source_id)
            remove_path(path, removed_paths)
    if all_memory or reset_sessions:
        remove_path(sessions_home(), removed_paths)
        remove_path(app_path("state", "active-session.json"), removed_paths)
    if all_memory or reset_tasks:
        remove_path(tasks_home(), removed_paths)
    if all_memory or reset_cache:
        remove_path(cache_home(), removed_paths)
    ensure_app_home()
    written_path = save_config(config)
    return {
        "kind": "memory-reset",
        "status": "reset",
        "config_path": str(written_path),
        "removed_paths": removed_paths,
        "sources_preserved": True,
        "sessions_reset": bool(all_memory or reset_sessions),
        "tasks_reset": bool(all_memory or reset_tasks),
        "cache_reset": bool(all_memory or reset_cache),
    }


def memory_path_payload() -> dict[str, Any]:
    return ensure_memory()


def unique_backup_id(title: str | None) -> str:
    base = sanitize_segment(title or "memory-backup")
    candidate = f"{base}-{timestamp_id()}"
    backups = memory_backups_home()
    if not (backups / candidate).exists():
        return candidate
    suffix = 2
    while (backups / f"{candidate}-{suffix}").exists():
        suffix += 1
    return f"{candidate}-{suffix}"


def timestamp_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def backup_file_inventory(root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = str(path.relative_to(root))
        data = path.read_bytes()
        items.append(
            {
                "path": relative,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return items


def public_backup(manifest: dict[str, Any], root: Path) -> dict[str, Any]:
    files = manifest.get("files") if isinstance(manifest.get("files"), list) else []
    return {
        "id": manifest.get("id"),
        "title": manifest.get("title"),
        "created_at": manifest.get("created_at"),
        "path": str(root),
        "storage": manifest.get("storage"),
        "remote_upload": manifest.get("remote_upload") is True,
        "encrypted": manifest.get("encrypted") is True,
        "sensitive_local_copy": manifest.get("sensitive_local_copy") is True,
        "package": manifest.get("package"),
        "package_name": manifest.get("package_name"),
        "file_count": len(files),
    }


def require_memory_backup(
    backup_id: str | None,
    *,
    backup_file: str | None = None,
    passphrase_env: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    if backup_file:
        package = Path(backup_file).expanduser().resolve()
        manifest = read_encrypted_backup_header(package, passphrase_env=passphrase_env)
        return package.parent, manifest
    item_id = sanitize_segment(backup_id or "")
    if not item_id:
        raise ValueError("memory backup requires a backup id")
    root = memory_backups_home() / item_id
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"memory backup not found: {item_id}")
    manifest = load_backup_manifest(manifest_path)
    if not manifest:
        raise ValueError(f"invalid memory backup manifest: {item_id}")
    return root, manifest


def load_backup_manifest(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def passphrase_from_env(passphrase_env: str | None) -> str:
    env_name = passphrase_env or "AGENT_DEVKIT_BACKUP_PASSPHRASE"
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", env_name):
        raise ValueError("--passphrase-env must be an environment variable name")
    value = os.environ.get(env_name)
    if not value:
        raise ValueError(f"memory backup passphrase environment variable is not set: {env_name}")
    if len(value) < 8:
        raise ValueError("memory backup passphrase must have at least 8 characters")
    return value


def write_encrypted_backup_package(package_path: Path, memory_dir: Path, manifest: dict[str, Any], passphrase: str) -> None:
    tar_bytes = memory_tar_bytes(memory_dir)
    salt = os.urandom(16)
    nonce = os.urandom(16)
    key = derive_backup_key(passphrase, salt)
    ciphertext = xor_bytes(tar_bytes, key, nonce)
    header = {
        "schema_version": BACKUP_PACKAGE_SCHEMA_VERSION,
        "algorithm": BACKUP_PACKAGE_ALGORITHM,
        "kdf": "PBKDF2-HMAC-SHA256",
        "iterations": 200_000,
        "salt": base64.b64encode(salt).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "manifest": {key: value for key, value in manifest.items() if key != "files"},
        "files": manifest.get("files") or [],
    }
    header_bytes = json.dumps(header, ensure_ascii=False, sort_keys=True).encode("utf-8")
    tag = hmac.new(key, header_bytes + ciphertext, hashlib.sha256).hexdigest()
    envelope = {
        "schema_version": BACKUP_PACKAGE_SCHEMA_VERSION,
        "header": header,
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        "tag": tag,
    }
    package_path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_encrypted_backup_header(package_path: Path, *, passphrase_env: str | None = None) -> dict[str, Any]:
    envelope = read_backup_package(package_path)
    header = envelope["header"]
    manifest = header.get("manifest") if isinstance(header.get("manifest"), dict) else {}
    payload = dict(manifest)
    payload["files"] = header.get("files") if isinstance(header.get("files"), list) else []
    payload["encrypted"] = True
    payload["sensitive_local_copy"] = False
    payload["package"] = str(package_path)
    payload["package_name"] = package_path.name
    payload.setdefault("id", package_path.stem)
    payload.setdefault("title", package_path.stem)
    return payload


def extract_encrypted_backup_package(package_path: Path, target: Path, passphrase: str) -> None:
    envelope = read_backup_package(package_path)
    header = envelope["header"]
    salt = base64.b64decode(header["salt"])
    nonce = base64.b64decode(header["nonce"])
    ciphertext = base64.b64decode(envelope["ciphertext"])
    key = derive_backup_key(passphrase, salt)
    header_bytes = json.dumps(header, ensure_ascii=False, sort_keys=True).encode("utf-8")
    expected_tag = hmac.new(key, header_bytes + ciphertext, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_tag, str(envelope.get("tag") or "")):
        raise ValueError("memory backup package integrity check failed")
    tar_bytes = xor_bytes(ciphertext, key, nonce)
    extract_memory_tar(tar_bytes, target)


def read_backup_package(package_path: Path) -> dict[str, Any]:
    if not package_path.exists():
        raise ValueError(f"memory backup package not found: {package_path}")
    try:
        envelope = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid memory backup package: {package_path}") from exc
    if not isinstance(envelope, dict) or envelope.get("schema_version") != BACKUP_PACKAGE_SCHEMA_VERSION:
        raise ValueError(f"unsupported memory backup package: {package_path}")
    header = envelope.get("header")
    if not isinstance(header, dict) or header.get("algorithm") != BACKUP_PACKAGE_ALGORITHM:
        raise ValueError(f"unsupported memory backup package algorithm: {package_path}")
    return envelope


def memory_tar_bytes(memory_dir: Path) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for path in sorted(item for item in memory_dir.rglob("*") if item.is_file()):
            archive.add(path, arcname=str(Path("memory") / path.relative_to(memory_dir)))
    return buffer.getvalue()


def extract_memory_tar(payload: bytes, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        for member in archive.getmembers():
            member_path = Path(member.name)
            if member_path.is_absolute() or ".." in member_path.parts or not member.name.startswith("memory/"):
                raise ValueError(f"unsafe path in memory backup package: {member.name}")
            if not member.isfile():
                continue
            output = target / member_path
            output.parent.mkdir(parents=True, exist_ok=True)
            extracted = archive.extractfile(member)
            if extracted is None:
                continue
            output.write_bytes(extracted.read())


def derive_backup_key(passphrase: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 200_000, dklen=32)


def xor_bytes(payload: bytes, key: bytes, nonce: bytes) -> bytes:
    output = bytearray()
    counter = 0
    for index in range(0, len(payload), 32):
        block = payload[index : index + 32]
        stream = hmac.new(key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest()
        output.extend(byte ^ stream[offset] for offset, byte in enumerate(block))
        counter += 1
    return bytes(output)


def package_path_from_manifest(backup_root: Path, manifest: dict[str, Any]) -> Path | None:
    raw = manifest.get("package")
    if isinstance(raw, str) and raw:
        return Path(raw).expanduser().resolve()
    package_name = manifest.get("package_name")
    if isinstance(package_name, str) and package_name:
        return backup_root / package_name
    candidates = sorted(backup_root.glob("*.adkmb"))
    return candidates[0] if candidates else None


def increment_bucket(bucket: dict[str, Any], key: str, now: str) -> None:
    item = bucket.setdefault(key, {"count": 0, "first_seen": now, "last_seen": now})
    item["count"] = int(item.get("count") or 0) + 1
    item.setdefault("first_seen", now)
    item["last_seen"] = now


def sorted_usage(bucket: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    for key, value in bucket.items():
        if isinstance(value, dict):
            items.append({"key": key, **value})
    return sorted(items, key=lambda item: (-int(item.get("count") or 0), item["key"]))


def remove_path(path: Path, removed_paths: list[str]) -> None:
    if path.exists():
        removed_paths.append(str(path))
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def sanitize_segment(value: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip(".-")
    return sanitized or "item"
