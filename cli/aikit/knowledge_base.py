"""File-first shared knowledge base commands."""

from __future__ import annotations

import json
import hashlib
import re
import secrets
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.aikit.errors import DevKitError
from cli.aikit.memory import redact_secrets
from cli.aikit.prompt_injection import external_content_block


KNOWLEDGE_SCHEMA_VERSION = "agent-devkit.knowledge/v1"
KNOWLEDGE_BASE_SCHEMA_VERSION = "agent-devkit.knowledge-base/v1"
DEFAULT_KB_DIR = "knowledge-base"
TOKEN_SCOPES = ("read", "contribute", "review", "admin", "owner")
KNOWLEDGE_PROVIDER_ALIASES = {
    "local": "knowledge-local",
    "filesystem": "knowledge-local",
    "github": "knowledge-github",
    "s3": "knowledge-s3",
    "supabase": "knowledge-supabase",
    "google-drive": "knowledge-google-drive",
    "drive": "knowledge-google-drive",
    "sharepoint": "knowledge-sharepoint",
    "onedrive": "knowledge-onedrive",
    "notion": "knowledge-notion",
    "obsidian": "knowledge-obsidian",
    "vector": "knowledge-vector",
}
KNOWLEDGE_PROVIDERS = set(KNOWLEDGE_PROVIDER_ALIASES.values())
ENTRY_DIRS = (
    "runbooks",
    "troubleshooting",
    "api-docs",
    "architecture-decisions",
    "incident-learnings",
    "automation-patterns",
    "provider-configs",
)
SECRET_PATTERN = re.compile(r"(token|secret|password|api[_-]?key|pat)\s*[:=]\s*\S+", re.IGNORECASE)
PII_PATTERN = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PERSONAL_MEMORY_PATTERN = re.compile(
    r"\b(meu nome|minha personalidade|minha prefer[eê]ncia|minhas prefer[eê]ncias|"
    r"prefiro|gosto de ser chamado|me chame de|chame-me de|responda para mim)\b",
    re.IGNORECASE,
)
CONVERSATIONAL_TOKENS = {
    "bom",
    "dia",
    "boa",
    "tarde",
    "noite",
    "ok",
    "obrigado",
    "obrigada",
    "valeu",
    "beleza",
    "perfeito",
    "entendi",
    "sim",
    "nao",
    "não",
    "thanks",
    "thank",
    "you",
    "hello",
    "hi",
}
REUSABLE_KNOWLEDGE_TOKENS = {
    "api",
    "arquitetura",
    "automacao",
    "automation",
    "comando",
    "configuracao",
    "configuração",
    "decisao",
    "decisão",
    "deploy",
    "diagnostico",
    "diagnóstico",
    "docker",
    "erro",
    "incident",
    "incidente",
    "incidentes",
    "integracao",
    "integração",
    "knowledge",
    "padrao",
    "padrão",
    "passo",
    "procedimento",
    "provider",
    "qa",
    "reutilizavel",
    "reutilizável",
    "reusable",
    "runbook",
    "solucao",
    "solução",
    "support",
    "teste",
    "troubleshooting",
    "workflow",
}


def knowledge_init(project: Path | None = None, *, force: bool = False) -> dict[str, Any]:
    root = knowledge_root(project)
    manifest = root / "kb.yaml"
    if manifest.exists() and not force:
        return knowledge_doctor(project)
    create_structure(root)
    write_yaml(manifest, default_manifest())
    (root / "README.md").write_text("# Knowledge Base\n\nFile-first shared Agent DevKit knowledge base.\n", encoding="utf-8")
    for policy in ("contribution-policy", "review-policy", "retention-policy", "security-policy"):
        (root / "policies" / f"{policy}.md").write_text(f"# {policy.replace('-', ' ').title()}\n\nDraft policy.\n", encoding="utf-8")
    rebuild_lexical_index(root)
    return {
        "kind": "knowledge",
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "status": "initialized",
        "path": str(root),
        "manifest": str(manifest),
    }


def knowledge_base_create(project: Path | None = None, *, provider: str | None = None, force: bool = False) -> dict[str, Any]:
    init = knowledge_init(project, force=force)
    root = knowledge_root(project)
    manifest = read_manifest(root)
    provider_id = normalize_knowledge_provider(provider or (manifest.get("storage") or {}).get("provider") or "local")
    manifest["schema_version"] = KNOWLEDGE_BASE_SCHEMA_VERSION
    manifest["storage"] = {"provider": provider_id, "location": DEFAULT_KB_DIR}
    manifest["permissions"] = token_permissions()
    manifest["updated_at"] = now_iso()
    write_yaml(root / "kb.yaml", manifest)
    tokens = ensure_token_refs(root)
    return {
        "kind": "knowledge-base",
        "schema_version": KNOWLEDGE_BASE_SCHEMA_VERSION,
        "status": "created" if init.get("status") == "initialized" else "ok",
        "path": str(root),
        "kb": public_manifest(manifest),
        "tokens": public_tokens(tokens),
        "stored_values": False,
    }


def knowledge_base_join(
    kb_id: str | None,
    project: Path | None = None,
    *,
    provider: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    if not kb_id:
        raise DevKitError("knowledge-base join requires a kb_id")
    payload = knowledge_base_create(project, provider=provider, force=force)
    root = knowledge_root(project)
    manifest = read_manifest(root)
    manifest["kb_id"] = kb_id
    manifest["updated_at"] = now_iso()
    manifest["sync"] = {
        "mode": "local-config-only",
        "remote_connected": False,
        "requires_token": True,
    }
    write_yaml(root / "kb.yaml", manifest)
    return {
        **payload,
        "status": "joined",
        "kb": public_manifest(manifest),
        "remote_connected": False,
        "next_steps": [
            "Configure provider credentials by reference before remote sync.",
            "Use `agent knowledge-base tokens` to inspect required token refs without exposing values.",
        ],
    }


def knowledge_base_status(project: Path | None = None) -> dict[str, Any]:
    root = require_knowledge_root(project)
    manifest = read_manifest(root)
    tokens = ensure_token_refs(root)
    doctor = knowledge_doctor(project)
    return {
        "kind": "knowledge-base",
        "schema_version": KNOWLEDGE_BASE_SCHEMA_VERSION,
        "status": "ok" if doctor.get("status") == "ok" else "blocked",
        "path": str(root),
        "kb": public_manifest(manifest),
        "tokens": public_tokens(tokens),
        "checks": doctor.get("checks") or [],
        "stored_values": False,
    }


def knowledge_base_tokens(project: Path | None = None) -> dict[str, Any]:
    root = require_knowledge_root(project)
    tokens = ensure_token_refs(root)
    return {
        "kind": "knowledge-base-tokens",
        "schema_version": KNOWLEDGE_BASE_SCHEMA_VERSION,
        "status": "ok",
        "path": str(tokens_path(root)),
        "tokens": public_tokens(tokens),
        "stored_values": False,
    }


def knowledge_base_rotate_token(scope: str | None, project: Path | None = None) -> dict[str, Any]:
    token_scope = require_scope(scope)
    root = require_knowledge_root(project)
    tokens = ensure_token_refs(root)
    tokens["tokens"][token_scope] = token_ref(token_scope)
    tokens["updated_at"] = now_iso()
    write_json(tokens_path(root), tokens)
    return {
        "kind": "knowledge-base-token",
        "schema_version": KNOWLEDGE_BASE_SCHEMA_VERSION,
        "status": "rotated",
        "scope": token_scope,
        "token": public_token(token_scope, tokens["tokens"][token_scope]),
        "stored_values": False,
    }


def knowledge_doctor(project: Path | None = None) -> dict[str, Any]:
    root = knowledge_root(project)
    checks = [
        {"id": "kb-root-exists", "status": "passed" if root.exists() else "failed"},
        {"id": "manifest-exists", "status": "passed" if (root / "kb.yaml").exists() else "failed"},
        {"id": "entries-dir-exists", "status": "passed" if (root / "entries").exists() else "failed"},
        {"id": "snapshots-dir-exists", "status": "passed" if (root / "snapshots" / "pending").exists() else "failed"},
        {"id": "lexical-index-exists", "status": "passed" if (root / "indexes" / "lexical.json").exists() else "failed"},
        {"id": "semantic-index-manifest-exists", "status": "passed" if (root / "indexes" / "semantic.json").exists() else "failed"},
        {"id": "chunks-index-exists", "status": "passed" if (root / "indexes" / "chunks.jsonl").exists() else "failed"},
    ]
    findings = scan_tree(root) if root.exists() else []
    checks.append({"id": "no-secret-or-pii", "status": "passed" if not findings else "failed"})
    return {
        "kind": "knowledge-doctor",
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "status": "ok" if all(check["status"] == "passed" for check in checks) else "blocked",
        "path": str(root),
        "checks": checks,
        "findings": findings[:20],
    }


def knowledge_search(query: str | None, project: Path | None = None) -> dict[str, Any]:
    if not query:
        raise DevKitError("knowledge search requires a query")
    root = require_knowledge_root(project)
    index_path = root / "indexes" / "lexical.json"
    if not index_path.exists():
        rebuild_lexical_index(root)
    index = json.loads(index_path.read_text(encoding="utf-8"))
    tokens = tokenize(query)
    results = []
    for item in index.get("items") or []:
        item_tokens = set(item.get("tokens") or [])
        score = len(tokens & item_tokens)
        if score:
            results.append({"path": item.get("path"), "title": item.get("title"), "score": score})
    results.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
    return {
        "kind": "knowledge-search",
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "status": "ok",
        "query": query,
        "count": len(results),
        "items": results[:20],
    }


def knowledge_index(project: Path | None = None) -> dict[str, Any]:
    root = require_knowledge_root(project)
    path = rebuild_lexical_index(root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "kind": "knowledge-index",
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "status": "rebuilt",
        "path": str(path),
        "count": len(payload.get("items") or []),
    }


def knowledge_snapshot_list(project: Path | None = None) -> dict[str, Any]:
    root = require_knowledge_root(project)
    items = []
    for bucket in ("pending", "accepted", "rejected"):
        folder = root / "snapshots" / bucket
        for path in sorted(folder.glob("*.md")):
            items.append(snapshot_item(root, path, bucket))
    return {
        "kind": "knowledge-snapshots",
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "status": "ok",
        "path": str(root / "snapshots"),
        "count": len(items),
        "items": items,
    }


def knowledge_snapshot_show(snapshot_id: str | None, project: Path | None = None) -> dict[str, Any]:
    root = require_knowledge_root(project)
    path, bucket = find_snapshot(root, snapshot_id)
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "kind": "knowledge-snapshot",
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "status": bucket,
        "snapshot_id": path.stem,
        "path": str(path),
        "snapshot": snapshot_item(root, path, bucket),
        "content": text,
    }


def knowledge_snapshot_score(snapshot_id: str | None, project: Path | None = None) -> dict[str, Any]:
    root = require_knowledge_root(project)
    path, bucket = find_snapshot(root, snapshot_id)
    text = path.read_text(encoding="utf-8", errors="replace")
    metadata = read_snapshot_metadata(root, bucket, path.stem)
    metadata_findings = metadata.get("findings") if isinstance(metadata.get("findings"), list) else []
    findings = [
        *metadata_findings,
        *scan_text(text),
        *knowledge_policy_findings(text),
        *duplicate_snapshot_findings(root, path.stem, text),
    ]
    block = external_content_block(f"knowledge-snapshot:{path.stem}", "markdown", text)
    if block["severity"] != "none":
        findings.append({"reason": "prompt-injection", "severity": block["severity"], "markers": block["detected_injection_markers"]})
    tokens = tokenize(text)
    positive = min(60, len(tokens))
    penalties = len(findings) * 25
    score = max(0, min(100, 40 + positive - penalties))
    decision = "blocked" if findings else ("review" if score < 70 else "submit")
    return {
        "kind": "knowledge-snapshot-score",
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "status": "ok",
        "snapshot_id": path.stem,
        "bucket": bucket,
        "score": score,
        "decision": decision,
        "findings": findings,
        "prompt_injection": {
            "severity": block["severity"],
            "markers": block["detected_injection_markers"],
        },
    }


def knowledge_snapshot_create(
    *,
    title: str | None,
    content: str | None,
    from_file: str | None,
    entry_type: str | None,
    project: Path | None = None,
) -> dict[str, Any]:
    root = require_knowledge_root(project)
    raw_content = snapshot_content(content, from_file)
    if not title:
        raise DevKitError("knowledge snapshot create requires --title")
    findings = scan_text(raw_content)
    block = external_content_block("knowledge-snapshot", "markdown", raw_content)
    snapshot_id = slugify(title)
    path = root / "snapshots" / "pending" / f"{snapshot_id}.md"
    if path.exists():
        snapshot_id = f"{snapshot_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        path = root / "snapshots" / "pending" / f"{snapshot_id}.md"
    frontmatter = {
        "snapshot_id": snapshot_id,
        "title": title,
        "type": entry_type or "runbook",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "prompt_injection_severity": block["severity"],
    }
    sanitized_content = sanitize_snapshot_content(raw_content)
    body = render_snapshot(frontmatter, sanitized_content)
    path.write_text(body, encoding="utf-8")
    write_json(
        snapshot_metadata_path(root, "pending", snapshot_id),
        {
            "schema_version": KNOWLEDGE_SCHEMA_VERSION,
            "snapshot_id": snapshot_id,
            "title": title,
            "type": entry_type or "runbook",
            "status": "pending",
            "findings": findings,
            "prompt_injection": {
                "severity": block["severity"],
                "markers": block["detected_injection_markers"],
            },
            "created_at": frontmatter["created_at"],
        },
    )
    return {
        "kind": "knowledge-snapshot",
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "status": "created",
        "snapshot_id": snapshot_id,
        "path": str(path),
        "findings": findings,
        "prompt_injection": {
            "severity": block["severity"],
            "markers": block["detected_injection_markers"],
        },
        "review_required": True,
    }


def knowledge_snapshot_submit(snapshot_id: str | None, project: Path | None = None) -> dict[str, Any]:
    root = require_knowledge_root(project)
    path = snapshot_path(root, "pending", require_snapshot_id(snapshot_id))
    score = knowledge_snapshot_score(path.stem, project)
    if score["decision"] == "blocked":
        return {
            "kind": "knowledge-snapshot-submit",
            "schema_version": KNOWLEDGE_SCHEMA_VERSION,
            "status": "blocked",
            "snapshot_id": path.stem,
            "score": score,
            "reason": "snapshot_score_blocked",
        }
    return {
        "kind": "knowledge-snapshot-submit",
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "status": "pending-review",
        "snapshot_id": path.stem,
        "path": str(path),
        "score": score,
        "remote_connected": False,
        "review_required": True,
        "next_steps": [f"Review with `agent knowledge review {path.stem}`."],
    }


def knowledge_review_list(project: Path | None = None) -> dict[str, Any]:
    root = require_knowledge_root(project)
    items = []
    for bucket in ("pending", "approved", "rejected"):
        folder = root / "reviews" / bucket
        for path in sorted(folder.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                items.append({"path": str(path.relative_to(root)), "bucket": bucket, **payload})
    return {
        "kind": "knowledge-reviews",
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "status": "ok",
        "path": str(root / "reviews"),
        "count": len(items),
        "items": items,
    }


def knowledge_review(snapshot_id: str | None, project: Path | None = None, *, persist: bool = True) -> dict[str, Any]:
    if not snapshot_id:
        raise DevKitError("knowledge review requires a snapshot id")
    root = require_knowledge_root(project)
    path = snapshot_path(root, "pending", snapshot_id)
    text = path.read_text(encoding="utf-8")
    metadata = read_snapshot_metadata(root, "pending", path.stem)
    metadata_findings = metadata.get("findings") if isinstance(metadata.get("findings"), list) else []
    findings = [
        *metadata_findings,
        *scan_text(text),
        *knowledge_policy_findings(text),
        *duplicate_snapshot_findings(root, path.stem, text),
    ]
    block = external_content_block(f"knowledge-snapshot:{snapshot_id}", "markdown", text)
    if block["severity"] != "none":
        findings.append({"reason": "prompt-injection", "severity": block["severity"], "markers": block["detected_injection_markers"]})
    passed = not findings
    review_payload = {
        "snapshot_id": snapshot_id,
        "status": "approved" if passed else "rejected",
        "findings": findings,
        "prompt_injection": {
            "severity": block["severity"],
            "markers": block["detected_injection_markers"],
        },
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    review_path = None
    if persist:
        review_dir = root / "reviews" / ("approved" if passed else "rejected")
        review_dir.mkdir(parents=True, exist_ok=True)
        review_path = review_dir / f"{snapshot_id}.json"
        review_path.write_text(json.dumps(review_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_knowledge_audit(
            root,
            event="review",
            snapshot_id=snapshot_id,
            decision=review_payload["status"],
            actor="knowledge-reviewer",
            content=text,
            findings=findings,
            metadata={
                "review_path": str(review_path.relative_to(root)),
                "prompt_injection": review_payload["prompt_injection"],
            },
        )
    return {
        "kind": "knowledge-review",
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "status": "approved" if passed else "rejected",
        "snapshot_id": snapshot_id,
        "review": review_payload,
        "persisted": persist,
        "path": str(review_path) if review_path else None,
    }


def knowledge_curate(project: Path | None = None) -> dict[str, Any]:
    root = require_knowledge_root(project)
    snapshot_items = knowledge_snapshot_list(project)["items"]
    titles: dict[str, list[dict[str, Any]]] = {}
    for item in snapshot_items:
        title = str(item.get("title") or item.get("snapshot_id") or "").strip().lower()
        if title:
            titles.setdefault(title, []).append(item)
    findings = [
        {
            "reason": "duplicate-title",
            "title": title,
            "paths": [str(item.get("path")) for item in items],
        }
        for title, items in sorted(titles.items())
        if len(items) > 1
    ]
    index = knowledge_index(project)
    return {
        "kind": "knowledge-curation",
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "status": "ok",
        "path": str(root),
        "findings": findings,
        "index": {"status": index["status"], "count": index["count"]},
        "next_steps": ["Review duplicate or obsolete entries before publishing curatorial changes."],
    }


def knowledge_publish(snapshot_id: str | None, project: Path | None = None, *, yes: bool = False, owner_agent: str | None = None) -> dict[str, Any]:
    if not snapshot_id:
        raise DevKitError("knowledge publish requires a snapshot id")
    root = require_knowledge_root(project)
    pending = snapshot_path(root, "pending", snapshot_id)
    owner_required = owner_agent_required(root)
    if yes and owner_agent != owner_required:
        return {
            "kind": "knowledge-publish",
            "schema_version": KNOWLEDGE_SCHEMA_VERSION,
            "status": "blocked",
            "snapshot_id": snapshot_id,
            "reason": "owner_agent_required",
            "owner_agent_required": owner_required,
            "owner_agent": owner_agent,
            "exit_code": 2,
        }
    review = knowledge_review(snapshot_id, project, persist=yes)
    if review["status"] != "approved":
        return {
            "kind": "knowledge-publish",
            "schema_version": KNOWLEDGE_SCHEMA_VERSION,
            "status": "blocked",
            "snapshot_id": snapshot_id,
            "review": review,
            "reason": "snapshot_review_failed",
        }
    if not yes:
        return {
            "kind": "knowledge-publish",
            "schema_version": KNOWLEDGE_SCHEMA_VERSION,
            "status": "planned",
            "snapshot_id": snapshot_id,
            "review": review,
            "owner_agent_required": owner_required,
            "next_steps": ["Re-run with `--yes --owner-agent knowledge-owner` to publish this approved snapshot locally."],
        }
    accepted = root / "snapshots" / "accepted" / pending.name
    accepted.parent.mkdir(parents=True, exist_ok=True)
    content = pending.read_text(encoding="utf-8", errors="replace")
    shutil.move(str(pending), accepted)
    pending_metadata = snapshot_metadata_path(root, "pending", snapshot_id)
    if pending_metadata.exists():
        accepted_metadata = snapshot_metadata_path(root, "accepted", snapshot_id)
        accepted_metadata.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(pending_metadata), accepted_metadata)
    rebuild_lexical_index(root)
    write_knowledge_audit(
        root,
        event="publish",
        snapshot_id=snapshot_id,
        decision="published",
        actor=owner_required,
        content=content,
        findings=(review.get("review") or {}).get("findings") or [],
        metadata={
            "accepted_path": str(accepted.relative_to(root)),
            "review_status": review.get("status"),
        },
    )
    return {
        "kind": "knowledge-publish",
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "status": "published",
        "snapshot_id": snapshot_id,
        "path": str(accepted),
        "review": review,
    }


def knowledge_sync(project: Path | None = None) -> dict[str, Any]:
    root = require_knowledge_root(project)
    manifest = read_manifest(root)
    storage = manifest.get("storage") if isinstance(manifest.get("storage"), dict) else {}
    provider = storage.get("provider") or "knowledge-local"
    if provider == "knowledge-local":
        return {
            "kind": "knowledge-sync",
            "schema_version": KNOWLEDGE_SCHEMA_VERSION,
            "status": "local-only",
            "executed": False,
            "provider": provider,
            "message": "Local file-first knowledge base does not require remote sync.",
        }
    return {
        "kind": "knowledge-sync",
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "status": "planned",
        "executed": False,
        "provider": provider,
        "remote_connected": False,
        "next_steps": ["Configure provider credentials by reference and opt in before remote sync."],
    }


def owner_agent_required(root: Path) -> str:
    manifest = read_manifest(root)
    return str(manifest.get("owner_agent") or "knowledge-owner")


def knowledge_root(project: Path | None = None) -> Path:
    return (project or Path.cwd()).resolve() / DEFAULT_KB_DIR


def require_knowledge_root(project: Path | None = None) -> Path:
    root = knowledge_root(project)
    if not (root / "kb.yaml").exists():
        raise DevKitError("knowledge base not initialized. Run `agent knowledge init` first.")
    return root


def create_structure(root: Path) -> None:
    for relative in [
        "policies",
        "entries",
        "snapshots/pending",
        "snapshots/accepted",
        "snapshots/rejected",
        "reviews/pending",
        "reviews/approved",
        "reviews/rejected",
        "indexes",
        "audit",
        "manifests",
    ]:
        (root / relative).mkdir(parents=True, exist_ok=True)
    for entry_dir in ENTRY_DIRS:
        (root / "entries" / entry_dir).mkdir(parents=True, exist_ok=True)
    initialize_derived_indexes(root)


def default_manifest() -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": KNOWLEDGE_BASE_SCHEMA_VERSION,
        "kb_id": new_kb_id(),
        "name": "Local Knowledge Base",
        "description": "File-first shared knowledge base",
        "owner_agent": "knowledge-owner",
        "storage": {"provider": "knowledge-local", "location": DEFAULT_KB_DIR},
        "indexes": {"lexical": {"enabled": True}, "semantic": {"enabled": False, "provider": None}},
        "cache": {"local_ttl_minutes": 1440, "remote_ttl_minutes": 240},
        "policies": {
            "contribution": "policies/contribution-policy.md",
            "review": "policies/review-policy.md",
            "security": "policies/security-policy.md",
        },
        "permissions": token_permissions(),
        "created_at": now,
        "updated_at": now,
    }


def new_kb_id() -> str:
    return f"kb_{secrets.token_hex(10)}"


def token_permissions() -> dict[str, str]:
    return {scope: f"secret-ref:knowledge-base/{scope}" for scope in TOKEN_SCOPES}


def tokens_path(root: Path) -> Path:
    return root / "manifests" / "tokens.json"


def ensure_token_refs(root: Path) -> dict[str, Any]:
    path = tokens_path(root)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}
    tokens = data.get("tokens") if isinstance(data.get("tokens"), dict) else {}
    changed = False
    for scope in TOKEN_SCOPES:
        if not isinstance(tokens.get(scope), dict):
            tokens[scope] = token_ref(scope)
            changed = True
    payload = {
        "schema_version": KNOWLEDGE_BASE_SCHEMA_VERSION,
        "stored_values": False,
        "tokens": tokens,
        "updated_at": data.get("updated_at") or now_iso(),
    }
    if changed or not path.exists():
        write_json(path, payload)
    return payload


def token_ref(scope: str) -> dict[str, Any]:
    return {
        "scope": scope,
        "ref": f"secret-ref:knowledge-base/{scope}",
        "fingerprint": secrets.token_hex(8),
        "value_stored": False,
        "rotated_at": now_iso(),
    }


def public_tokens(payload: dict[str, Any]) -> list[dict[str, Any]]:
    tokens = payload.get("tokens") if isinstance(payload.get("tokens"), dict) else {}
    return [public_token(scope, tokens.get(scope) if isinstance(tokens.get(scope), dict) else {}) for scope in TOKEN_SCOPES]


def public_token(scope: str, token: dict[str, Any]) -> dict[str, Any]:
    return {
        "scope": scope,
        "ref": token.get("ref") or f"secret-ref:knowledge-base/{scope}",
        "fingerprint": token.get("fingerprint"),
        "value_stored": False,
        "rotated_at": token.get("rotated_at"),
    }


def read_manifest(root: Path) -> dict[str, Any]:
    path = root / "kb.yaml"
    if not path.exists():
        raise DevKitError("knowledge base not initialized. Run `agent knowledge-base create` first.")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except ImportError:
        data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def public_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "kb_id": manifest.get("kb_id"),
        "name": manifest.get("name"),
        "description": manifest.get("description"),
        "owner_agent": manifest.get("owner_agent"),
        "storage": manifest.get("storage") or {},
        "indexes": manifest.get("indexes") or {},
        "cache": manifest.get("cache") or {},
        "permissions": manifest.get("permissions") or {},
        "created_at": manifest.get("created_at"),
        "updated_at": manifest.get("updated_at"),
    }


def require_scope(scope: str | None) -> str:
    if not scope:
        raise DevKitError("knowledge-base rotate-token requires a scope")
    value = scope.strip().lower()
    aliases = {"approve": "owner", "owner_key": "owner", "contribution": "contribute"}
    value = aliases.get(value, value)
    if value not in TOKEN_SCOPES:
        raise DevKitError(f"unsupported knowledge-base token scope: {scope}")
    return value


def normalize_knowledge_provider(provider: str | None) -> str:
    raw = (provider or "local").strip().lower()
    provider_id = KNOWLEDGE_PROVIDER_ALIASES.get(raw, raw)
    if provider_id not in KNOWLEDGE_PROVIDERS:
        supported = ", ".join(sorted(KNOWLEDGE_PROVIDER_ALIASES))
        raise DevKitError(f"unsupported knowledge provider: {provider}. Supported: {supported}")
    return provider_id


def rebuild_lexical_index(root: Path) -> Path:
    items = []
    for base in (root / "entries", root / "snapshots" / "accepted"):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".md", ".json", ".yaml", ".yml"}:
                text = path.read_text(encoding="utf-8", errors="replace")
                items.append({"path": str(path.relative_to(root)), "title": title_for(path, text), "tokens": sorted(tokenize(text))})
    payload = {"schema_version": KNOWLEDGE_SCHEMA_VERSION, "items": items, "rebuilt_at": datetime.now(timezone.utc).isoformat()}
    path = root / "indexes" / "lexical.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    initialize_derived_indexes(root)
    return path


def initialize_derived_indexes(root: Path) -> None:
    index_root = root / "indexes"
    index_root.mkdir(parents=True, exist_ok=True)
    semantic_path = index_root / "semantic.json"
    if not semantic_path.exists():
        payload = {
            "schema_version": KNOWLEDGE_SCHEMA_VERSION,
            "enabled": False,
            "provider": None,
            "derived": True,
            "items": [],
            "rebuilt_at": None,
        }
        semantic_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    chunks_path = index_root / "chunks.jsonl"
    if not chunks_path.exists():
        chunks_path.write_text("", encoding="utf-8")


def snapshot_content(content: str | None, from_file: str | None) -> str:
    if from_file:
        return Path(from_file).expanduser().resolve().read_text(encoding="utf-8", errors="replace")
    if content:
        return content
    raise DevKitError("knowledge snapshot create requires --content or --from-file")


def sanitize_snapshot_content(text: str) -> str:
    sanitized = redact_secrets(text)
    sanitized = SECRET_PATTERN.sub(lambda match: redact_secret_assignment(match.group(0)), sanitized)
    return PII_PATTERN.sub("[REDACTED_PII]", sanitized)


def redact_secret_assignment(value: str) -> str:
    separator = "=" if "=" in value else ":"
    prefix = value.split(separator, 1)[0].rstrip()
    return f"{prefix}{separator}[REDACTED_SECRET]"


def snapshot_path(root: Path, bucket: str, snapshot_id: str) -> Path:
    path = root / "snapshots" / bucket / f"{slugify(snapshot_id)}.md"
    if not path.exists():
        raise DevKitError(f"knowledge snapshot not found: {snapshot_id}")
    return path


def snapshot_metadata_path(root: Path, bucket: str, snapshot_id: str) -> Path:
    return root / "snapshots" / bucket / f"{slugify(snapshot_id)}.json"


def read_snapshot_metadata(root: Path, bucket: str, snapshot_id: str) -> dict[str, Any]:
    path = snapshot_metadata_path(root, bucket, snapshot_id)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def find_snapshot(root: Path, snapshot_id: str | None) -> tuple[Path, str]:
    item_id = require_snapshot_id(snapshot_id)
    for bucket in ("pending", "accepted", "rejected"):
        path = root / "snapshots" / bucket / f"{slugify(item_id)}.md"
        if path.exists():
            return path, bucket
    raise DevKitError(f"knowledge snapshot not found: {snapshot_id}")


def require_snapshot_id(snapshot_id: str | None) -> str:
    if not snapshot_id:
        raise DevKitError("knowledge snapshot id is required")
    return snapshot_id


def snapshot_item(root: Path, path: Path, bucket: str) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "snapshot_id": path.stem,
        "title": title_for(path, text),
        "bucket": bucket,
        "path": str(path.relative_to(root)),
        "bytes": path.stat().st_size,
    }


def render_snapshot(frontmatter: dict[str, Any], content: str) -> str:
    return "---\n" + "\n".join(f"{key}: {value}" for key, value in frontmatter.items()) + "\n---\n\n" + content.strip() + "\n"


def scan_tree(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".md", ".json", ".yaml", ".yml", ".txt"}:
            for finding in scan_text(path.read_text(encoding="utf-8", errors="replace")):
                findings.append({"path": str(path.relative_to(root)), **finding})
    return findings


def scan_text(text: str) -> list[dict[str, Any]]:
    findings = []
    if SECRET_PATTERN.search(text):
        findings.append({"reason": "secret-like-material"})
    if PII_PATTERN.search(text):
        findings.append({"reason": "pii-like-material"})
    block = external_content_block("knowledge-scan", "text", text)
    if block["severity"] != "none":
        findings.append({"reason": "prompt-injection", "severity": block["severity"], "markers": block["detected_injection_markers"]})
    return findings


def knowledge_policy_findings(text: str) -> list[dict[str, Any]]:
    body = snapshot_body(text)
    tokens = tokenize(body)
    if not tokens:
        return [{"reason": "low-recurring-utility", "detail": "empty-content"}]
    has_reusable_signal = bool(tokens & REUSABLE_KNOWLEDGE_TOKENS)
    findings: list[dict[str, Any]] = []
    if PERSONAL_MEMORY_PATTERN.search(body):
        findings.append({"reason": "personal-memory-content"})
    if len(tokens) < 6 and not has_reusable_signal:
        findings.append({"reason": "low-recurring-utility", "token_count": len(tokens)})
    if len(tokens) <= 14 and not has_reusable_signal and bool(tokens & CONVERSATIONAL_TOKENS):
        findings.append({"reason": "purely-conversational-content", "token_count": len(tokens)})
    return findings


def duplicate_snapshot_findings(root: Path, snapshot_id: str, text: str) -> list[dict[str, Any]]:
    current_fingerprint = content_fingerprint(snapshot_body(text))
    if not current_fingerprint:
        return []
    matches = []
    for bucket in ("accepted", "pending"):
        folder = root / "snapshots" / bucket
        for path in sorted(folder.glob("*.md")):
            if path.stem == slugify(snapshot_id):
                continue
            candidate_text = path.read_text(encoding="utf-8", errors="replace")
            if content_fingerprint(snapshot_body(candidate_text)) == current_fingerprint:
                matches.append(str(path.relative_to(root)))
    if not matches:
        return []
    return [{"reason": "duplicate-content", "matches": matches}]


def snapshot_body(text: str) -> str:
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return text
    parts = stripped.split("---", 2)
    if len(parts) >= 3:
        return parts[2]
    return text


def content_fingerprint(text: str) -> str:
    return " ".join(sorted(tokenize(text)))


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9_À-ÿ-]{2,}", text.lower()) if token}


def title_for(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or path.stem
    return path.stem


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "snapshot"


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    try:
        import yaml  # type: ignore

        text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    except ImportError:
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_knowledge_audit(
    root: Path,
    *,
    event: str,
    snapshot_id: str,
    decision: str,
    actor: str,
    content: str,
    findings: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
) -> Path:
    created_at = now_iso()
    safe_event = slugify(event)
    safe_snapshot = slugify(snapshot_id)
    path = root / "audit" / f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}-{safe_event}-{safe_snapshot}.json"
    payload = {
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "event": event,
        "snapshot_id": snapshot_id,
        "decision": decision,
        "actor": actor,
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "findings": findings,
        "metadata": metadata or {},
        "created_at": created_at,
    }
    write_json(path, payload)
    return path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
