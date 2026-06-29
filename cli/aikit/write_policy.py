"""Canonical write policy vocabulary used by the Agent DevKit runtime."""

from __future__ import annotations

from typing import Any


CANONICAL_WRITE_POLICIES = {
    "read_only",
    "dry_run",
    "output_only",
    "local_write",
    "local_config_write",
    "confirm",
    "blocked_by_default",
    "delegated",
}

LEGACY_WRITE_POLICY_ALIASES = {
    "read-only": "read_only",
    "delegated_read_only": "read_only",
    "ask_before_write": "confirm",
    "ask_before_creating_output_directory": "output_only",
    "generated_artifacts_only": "output_only",
    "create_new_version": "local_write",
    "template_version_write": "local_write",
    "local-write": "local_write",
    "local-config-write": "local_config_write",
}

AUTONOMOUS_SAFE_WRITE_POLICIES = {"read_only", "dry_run"}
CONFIRMATION_WRITE_POLICIES = {"confirm", "local_write", "local_config_write"}
BLOCKED_WRITE_POLICIES = {"blocked_by_default"}


def canonical_write_policies() -> set[str]:
    return set(CANONICAL_WRITE_POLICIES)


def legacy_write_policy_aliases() -> dict[str, str]:
    return dict(LEGACY_WRITE_POLICY_ALIASES)


def normalize_write_policy(value: Any, *, default: str = "read_only") -> str:
    raw = str(value or "").strip()
    if not raw:
        raw = default
    return LEGACY_WRITE_POLICY_ALIASES.get(raw, raw)


def is_known_write_policy(value: Any) -> bool:
    raw = str(value or "").strip()
    if not raw:
        return False
    return raw in CANONICAL_WRITE_POLICIES or raw in LEGACY_WRITE_POLICY_ALIASES


def is_autonomous_safe_write_policy(value: Any) -> bool:
    return normalize_write_policy(value) in AUTONOMOUS_SAFE_WRITE_POLICIES


def requires_runtime_confirmation(value: Any) -> bool:
    return normalize_write_policy(value) in CONFIRMATION_WRITE_POLICIES


def is_blocked_by_default(value: Any) -> bool:
    return normalize_write_policy(value) in BLOCKED_WRITE_POLICIES


def write_policy_metadata(value: Any, *, default: str = "read_only") -> dict[str, Any]:
    raw = str(value or "").strip() or default
    canonical = normalize_write_policy(raw, default=default)
    return {
        "raw": raw,
        "canonical": canonical,
        "known": is_known_write_policy(raw),
        "legacy": raw in LEGACY_WRITE_POLICY_ALIASES,
        "autonomous_safe": canonical in AUTONOMOUS_SAFE_WRITE_POLICIES,
        "requires_confirmation": canonical in CONFIRMATION_WRITE_POLICIES,
        "blocked_by_default": canonical in BLOCKED_WRITE_POLICIES,
    }


def coerce_write_policy_metadata(value: Any, *, default: str = "read_only") -> dict[str, Any]:
    if not isinstance(value, dict):
        return write_policy_metadata(value, default=default)

    canonical_hint = str(value.get("canonical") or "").strip()
    raw = str(value.get("raw") or "").strip() or canonical_hint or default
    canonical = canonical_hint or normalize_write_policy(raw, default=default)
    return {
        "raw": raw,
        "canonical": canonical,
        "known": canonical in CANONICAL_WRITE_POLICIES or is_known_write_policy(raw),
        "legacy": raw in LEGACY_WRITE_POLICY_ALIASES,
        "autonomous_safe": canonical in AUTONOMOUS_SAFE_WRITE_POLICIES,
        "requires_confirmation": canonical in CONFIRMATION_WRITE_POLICIES,
        "blocked_by_default": canonical in BLOCKED_WRITE_POLICIES,
    }


def write_policy_public_fields(value: Any, *, default: str = "read_only") -> dict[str, Any]:
    metadata = coerce_write_policy_metadata(value, default=default)
    return {
        "write_policy": metadata["canonical"],
        "write_policy_raw": metadata["raw"],
        "write_policy_metadata": metadata,
    }
