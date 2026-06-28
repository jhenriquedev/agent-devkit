"""Standard output payloads for agent runtime commands."""

from __future__ import annotations

from typing import Any


RUN_SCHEMA_VERSION = "ai-devkit.run/v1"
RUN_STATUSES = {"ok", "partial", "blocked", "failed"}


def run_payload(
    *,
    status: str,
    agent: dict[str, Any],
    capability: str,
    runner: str | None,
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
    providers: dict[str, Any] | None = None,
    fallback_applied: str | None = None,
    evidence: list[dict[str, Any]] | None = None,
    risks: list[str] | None = None,
    next_steps: list[str] | None = None,
    artifacts: list[dict[str, Any]] | None = None,
    guardrail: dict[str, Any] | None = None,
    error: str | None = None,
    exit_code: int | None = None,
) -> dict[str, Any]:
    """Build a stable, parseable `agent run` result payload."""

    if status not in RUN_STATUSES:
        raise ValueError(f"unsupported run status: {status}")

    payload: dict[str, Any] = {
        "kind": "run",
        "schema_version": RUN_SCHEMA_VERSION,
        "status": status,
        "ok": status == "ok",
        "agent": agent,
        "agent_id": agent.get("id"),
        "capability": capability,
        "capability_id": capability.split(".")[-1],
        "runner": runner,
        "stdout": stdout,
        "stderr": stderr,
        "returncode": returncode,
        "providers": normalize_providers(providers),
        "fallback_applied": fallback_applied,
        "evidence": evidence or [],
        "risks": risks or [],
        "next_steps": next_steps or [],
        "artifacts": artifacts or [],
    }
    if guardrail is not None:
        payload["guardrail"] = guardrail
    if error:
        payload["error"] = error
    if exit_code is not None:
        payload["exit_code"] = exit_code
    return payload


def normalize_providers(providers: dict[str, Any] | None) -> dict[str, Any]:
    result = dict(providers or {})
    result.setdefault("used", [])
    result.setdefault("missing", [])
    result.setdefault("skipped", [])
    return result
