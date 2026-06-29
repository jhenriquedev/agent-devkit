"""Execution guardrails for agent run."""

from __future__ import annotations

from typing import Any

from cli.aikit.write_policy import (
    is_blocked_by_default,
    is_known_write_policy,
    normalize_write_policy,
    requires_runtime_confirmation,
)


RUNTIME_CONFIRM_FLAG = "--confirm-execute"
RUNTIME_DANGEROUS_FLAG = "--allow-dangerous"
EXECUTE_FLAG = "--execute"
EXECUTE_INTENT_FLAGS = {
    EXECUTE_FLAG,
    "--yes-confirm",
    "--yes-save",
}


def evaluate_execution_guardrails(
    capability: dict[str, Any],
    capability_args: list[str],
) -> dict[str, Any]:
    """Return sanitized args and an optional blocked guardrail result."""

    sanitized_args = strip_runtime_flags(capability_args)
    raw_write_policy = capability.get("write_policy")
    write_policy = normalize_write_policy(raw_write_policy or "")
    execute_requested = any(flag in capability_args for flag in EXECUTE_INTENT_FLAGS)
    confirmed = RUNTIME_CONFIRM_FLAG in capability_args
    dangerous_allowed = RUNTIME_DANGEROUS_FLAG in capability_args

    if raw_write_policy and not is_known_write_policy(raw_write_policy):
        return {
            "ready": False,
            "args": sanitized_args,
            "reason": "unknown_write_policy",
            "write_policy": write_policy,
            "risks": [
                "Capability declares an unsupported write policy, so runtime safety semantics are ambiguous.",
            ],
            "next_steps": [
                "Fix the capability manifest to use a canonical write_policy before requesting execution.",
            ],
        }

    if execute_requested and is_blocked_by_default(write_policy) and not dangerous_allowed:
        return {
            "ready": False,
            "args": sanitized_args,
            "reason": "dangerous_by_default",
            "write_policy": write_policy,
            "risks": [
                "Capability is marked blocked_by_default and may represent a destructive or high-impact mutation.",
            ],
            "next_steps": [
                "Re-run with `--allow-dangerous --confirm-execute --execute` only after validating the operation plan, target, blast radius, and rollback path.",
            ],
        }

    if execute_requested and requires_runtime_confirmation(write_policy) and not confirmed:
        return {
            "ready": False,
            "args": sanitized_args,
            "reason": "missing_runtime_confirmation",
            "write_policy": write_policy,
            "risks": [
                "Capability requested real execution for a write policy that requires explicit runtime confirmation.",
            ],
            "next_steps": [
                "Re-run with `--confirm-execute` plus the capability execution flag after reviewing the dry-run output and confirming the target resource.",
            ],
        }

    return {
        "ready": True,
        "args": sanitized_args,
        "reason": None,
        "write_policy": write_policy,
        "risks": [],
        "next_steps": [],
    }


def strip_runtime_flags(args: list[str]) -> list[str]:
    return [arg for arg in args if arg not in {RUNTIME_CONFIRM_FLAG, RUNTIME_DANGEROUS_FLAG}]
