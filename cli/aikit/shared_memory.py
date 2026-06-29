"""Shared memory workspaces with owner-reviewed contributions."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.aikit.app_home import app_home, ensure_app_home
from cli.aikit.errors import DevKitError
from cli.aikit.knowledge_base import sanitize_snapshot_content, scan_text
from cli.aikit.prompt_injection import external_content_block


SHARED_MEMORY_SCHEMA_VERSION = "agent-devkit.shared-memory/v1"


def shared_memory_home() -> Path:
    ensure_app_home()
    path = app_home() / "shared-memory"
    path.mkdir(parents=True, exist_ok=True)
    return path


def shared_memory_create(title: str | None = None) -> dict[str, Any]:
    memory_id = slugify(title or "shared-memory")
    root = unique_workspace_path(memory_id)
    for relative in ("incoming", "reviews", "accepted", "rejected", "audit"):
        (root / relative).mkdir(parents=True, exist_ok=True)
    owner_key = new_key("own")
    contributor_key = new_key("contrib")
    manifest = {
        "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
        "id": root.name,
        "title": title or root.name,
        "owner": "local",
        "owner_key": owner_key,
        "contributor_key": contributor_key,
        "share_url": root.as_uri(),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "policy": {
            "contributors": "key-required",
            "publish": "owner-review-required",
            "accepted_visibility": "readable-by-url-holder",
        },
    }
    write_json(root / "manifest.json", manifest)
    return {
        "kind": "shared-memory",
        "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
        "status": "created",
        "memory": public_manifest(manifest),
        "path": str(root),
        "owner_access": {
            "key": owner_key,
            "role": "owner",
            "usage": "Required to publish reviewed submissions with --yes.",
        },
        "contributor_access": {
            "url": manifest["share_url"],
            "key": contributor_key,
            "role": "contributor",
        },
        "next_steps": [
            "Share contributor_access.url and contributor_access.key with another agent.",
            "Review submissions with `agent memory review <memory-id> <submission-id>`.",
            "Publish approved submissions with `agent memory publish <memory-id> <submission-id> --yes`.",
        ],
    }


def shared_memory_list() -> dict[str, Any]:
    items = []
    for manifest_path in sorted(shared_memory_home().glob("*/manifest.json")):
        try:
            manifest = read_json(manifest_path)
        except DevKitError:
            continue
        items.append(public_manifest(manifest))
    return {
        "kind": "shared-memories",
        "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
        "status": "ok",
        "home": str(shared_memory_home()),
        "items": items,
    }


def shared_memory_status(memory_id: str | None) -> dict[str, Any]:
    root, manifest = require_workspace(memory_id)
    return {
        "kind": "shared-memory",
        "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
        "status": "ok",
        "memory": public_manifest(manifest),
        "submissions": {
            "pending": count_files(root / "incoming"),
            "accepted": count_files(root / "accepted"),
            "rejected": count_files(root / "rejected"),
        },
        "path": str(root),
    }


def shared_memory_read(memory_id: str | None, entry_id: str | None = None, *, contributor_key: str | None = None) -> dict[str, Any]:
    root, manifest = require_workspace(memory_id)
    if contributor_key and contributor_key != manifest.get("contributor_key"):
        return {
            "kind": "shared-memory-read",
            "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
            "status": "blocked",
            "ok": False,
            "reason": "invalid-contributor-key",
            "memory_id": manifest.get("id"),
            "exit_code": 2,
        }
    role = "contributor" if contributor_key else "owner"
    accepted = root / "accepted"
    if entry_id:
        sid = require_id(entry_id, "entry id")
        path = accepted / f"{sid}.md"
        if not path.exists():
            raise DevKitError(f"shared memory accepted entry not found: {sid}")
        content = path.read_text(encoding="utf-8", errors="replace")
        return {
            "kind": "shared-memory-read",
            "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
            "status": "ok",
            "memory_id": manifest.get("id"),
            "role": role,
            "entry_id": sid,
            "path": str(path),
            "content": content,
            "items": [accepted_item(root, path)],
        }
    items = [accepted_item(root, path) for path in sorted(accepted.glob("*.md"))]
    return {
        "kind": "shared-memory-read",
        "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
        "status": "ok",
        "memory_id": manifest.get("id"),
        "role": role,
        "path": str(accepted),
        "count": len(items),
        "items": items,
    }


def shared_memory_submit(
    memory_id: str | None,
    *,
    title: str | None,
    content: str | None,
    contributor_key: str | None,
) -> dict[str, Any]:
    root, manifest = require_workspace(memory_id)
    if not contributor_key or contributor_key != manifest.get("contributor_key"):
        return {
            "kind": "shared-memory-submission",
            "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
            "status": "blocked",
            "ok": False,
            "reason": "invalid-contributor-key",
            "memory_id": manifest.get("id"),
            "exit_code": 2,
        }
    if not content:
        raise DevKitError("memory submit requires --content")
    submission_id = unique_submission_id(title or "submission", root / "incoming")
    block = external_content_block("shared-memory-submission", "markdown", content)
    findings = scan_text(content)
    metadata = {
        "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
        "memory_id": manifest.get("id"),
        "submission_id": submission_id,
        "title": title or submission_id,
        "status": "pending",
        "created_at": now_iso(),
        "findings": findings,
        "prompt_injection": {
            "severity": block["severity"],
            "markers": block["detected_injection_markers"],
        },
    }
    (root / "incoming" / f"{submission_id}.md").write_text(sanitize_snapshot_content(content).strip() + "\n", encoding="utf-8")
    write_json(root / "incoming" / f"{submission_id}.json", metadata)
    return {
        "kind": "shared-memory-submission",
        "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
        "status": "pending",
        "ok": True,
        "memory_id": manifest.get("id"),
        "submission_id": submission_id,
        "path": str(root / "incoming" / f"{submission_id}.md"),
        "review_required": True,
        "findings": findings,
        "prompt_injection": metadata["prompt_injection"],
    }


def shared_memory_review(memory_id: str | None, submission_id: str | None, *, persist: bool = True) -> dict[str, Any]:
    root, manifest = require_workspace(memory_id)
    sid = require_id(submission_id, "submission id")
    content_path = root / "incoming" / f"{sid}.md"
    if not content_path.exists():
        raise DevKitError(f"shared memory submission not found: {sid}")
    metadata = read_submission_metadata(root, sid)
    submission_findings = metadata.get("findings") if isinstance(metadata.get("findings"), list) else []
    content = content_path.read_text(encoding="utf-8", errors="replace")
    block = external_content_block(f"shared-memory:{sid}", "markdown", content)
    findings = [*submission_findings]
    if block["severity"] != "none":
        findings.append(
            {
                "reason": "prompt-injection",
                "severity": block["severity"],
                "markers": block["detected_injection_markers"],
            }
        )
    passed = not findings
    review = {
        "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
        "memory_id": manifest.get("id"),
        "submission_id": sid,
        "status": "approved" if passed else "rejected",
        "findings": findings,
        "reviewed_at": now_iso(),
        "prompt_injection": {
            "severity": block["severity"],
            "markers": block["detected_injection_markers"],
        },
    }
    review_path = None
    if persist:
        review_path = root / "reviews" / f"{sid}.json"
        write_json(review_path, review)
    return {
        "kind": "shared-memory-review",
        "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
        "status": review["status"],
        "memory_id": manifest.get("id"),
        "submission_id": sid,
        "review": review,
        "persisted": persist,
        "path": str(review_path) if review_path else None,
    }


def shared_memory_publish(
    memory_id: str | None,
    submission_id: str | None,
    *,
    yes: bool = False,
    owner_key: str | None = None,
) -> dict[str, Any]:
    root, manifest = require_workspace(memory_id)
    sid = require_id(submission_id, "submission id")
    if yes and owner_key != manifest.get("owner_key"):
        return {
            "kind": "shared-memory-publish",
            "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
            "status": "blocked",
            "memory_id": manifest.get("id"),
            "submission_id": sid,
            "reason": "owner_key_required",
            "exit_code": 2,
        }
    review = shared_memory_review(manifest.get("id"), sid, persist=yes)
    if review["status"] != "approved":
        return {
            "kind": "shared-memory-publish",
            "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
            "status": "blocked",
            "memory_id": manifest.get("id"),
            "submission_id": sid,
            "review": review,
            "reason": "review-rejected",
        }
    if not yes:
        return {
            "kind": "shared-memory-publish",
            "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
            "status": "planned",
            "memory_id": manifest.get("id"),
            "submission_id": sid,
            "review": review,
            "next_steps": ["Re-run with `--yes --owner-key <owner-key>` to publish into accepted shared memory."],
        }
    source = root / "incoming" / f"{sid}.md"
    target = root / "accepted" / f"{sid}.md"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    source.unlink(missing_ok=True)
    (root / "incoming" / f"{sid}.json").unlink(missing_ok=True)
    manifest["updated_at"] = now_iso()
    write_json(root / "manifest.json", manifest)
    return {
        "kind": "shared-memory-publish",
        "schema_version": SHARED_MEMORY_SCHEMA_VERSION,
        "status": "published",
        "memory_id": manifest.get("id"),
        "submission_id": sid,
        "path": str(target),
        "review": review,
    }


def require_workspace(memory_id: str | None) -> tuple[Path, dict[str, Any]]:
    item_id = require_id(memory_id, "memory id")
    root = shared_memory_home() / item_id
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise DevKitError(f"shared memory not found: {item_id}")
    return root, read_json(manifest_path)


def public_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "id": manifest.get("id"),
        "title": manifest.get("title"),
        "owner": manifest.get("owner"),
        "share_url": manifest.get("share_url"),
        "created_at": manifest.get("created_at"),
        "updated_at": manifest.get("updated_at"),
        "policy": manifest.get("policy") or {},
        "contributor_key_available": bool(manifest.get("contributor_key")),
    }
    return payload


def accepted_item(root: Path, path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "id": path.stem,
        "title": title_for(path, text),
        "path": str(path.relative_to(root)),
        "bytes": path.stat().st_size,
    }


def title_for(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or path.stem
    return path.stem


def unique_workspace_path(base_id: str) -> Path:
    home = shared_memory_home()
    candidate = home / base_id
    if not candidate.exists():
        return candidate
    index = 2
    while (home / f"{base_id}-{index}").exists():
        index += 1
    return home / f"{base_id}-{index}"


def unique_submission_id(title: str, folder: Path) -> str:
    base = slugify(title)
    candidate = base
    index = 2
    while (folder / f"{candidate}.md").exists() or (folder / f"{candidate}.json").exists():
        candidate = f"{base}-{index}"
        index += 1
    return candidate


def require_id(value: str | None, label: str) -> str:
    item_id = slugify(value or "")
    if not item_id:
        raise DevKitError(f"{label} is required")
    return item_id


def slugify(value: str) -> str:
    import re

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(value).strip().lower()).strip("-")
    return slug


def new_key(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(24)}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def count_files(path: Path) -> int:
    return len([item for item in path.glob("*.md") if item.is_file()])


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DevKitError(f"invalid shared memory file: {path}") from exc
    return payload if isinstance(payload, dict) else {}


def read_submission_metadata(root: Path, submission_id: str) -> dict[str, Any]:
    path = root / "incoming" / f"{submission_id}.json"
    if not path.exists():
        return {}
    return read_json(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
