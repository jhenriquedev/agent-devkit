"""Standard output payloads for agent runtime commands."""

from __future__ import annotations

from typing import Any

from cli.aikit.write_policy import coerce_write_policy_metadata, write_policy_public_fields


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
    artifacts: list[Any] | None = None,
    guardrail: dict[str, Any] | None = None,
    error: str | None = None,
    reason: str | None = None,
    exit_code: int | None = None,
    origin: str = "core",
    request_id: str | None = None,
    data: dict[str, Any] | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a stable, parseable `agent run` result payload."""

    if status not in RUN_STATUSES:
        raise ValueError(f"unsupported run status: {status}")

    policy_metadata = coerce_write_policy_metadata(policy or {})
    payload: dict[str, Any] = {
        "kind": "run",
        "schema_version": RUN_SCHEMA_VERSION,
        "status": status,
        "ok": status == "ok",
        "agent": agent,
        "agent_id": agent.get("id"),
        "capability": capability,
        "capability_id": capability.split(".")[-1],
        "origin": origin,
        "request_id": request_id,
        "runner": runner,
        "stdout": stdout,
        "stderr": stderr,
        "returncode": returncode,
        "data": data or {},
        "policy": policy_metadata,
        **write_policy_public_fields(policy_metadata),
        "providers": normalize_providers(providers),
        "fallback_applied": fallback_applied,
        "evidence": evidence or [],
        "risks": risks or [],
        "next_steps": next_steps or [],
        "artifacts": normalize_artifacts(artifacts),
    }
    if guardrail is not None:
        payload["guardrail"] = guardrail
    if error:
        payload["error"] = error
    if reason:
        payload["reason"] = reason
    if exit_code is not None:
        payload["exit_code"] = exit_code
    return payload


def normalize_providers(providers: dict[str, Any] | None) -> dict[str, Any]:
    result = dict(providers or {})
    result.setdefault("used", [])
    result.setdefault("missing", [])
    result.setdefault("skipped", [])
    result.setdefault("details", [])
    return result


def normalize_artifacts(artifacts: list[Any] | None) -> list[dict[str, Any]]:
    result = []
    for item in artifacts or []:
        if isinstance(item, str):
            result.append(
                {
                    "path": item,
                    "kind": artifact_kind(item),
                    "description": "",
                    "sensitive": False,
                    "created": None,
                }
            )
            continue
        if isinstance(item, dict):
            path = str(item.get("path") or item.get("ref") or "").strip()
            result.append(
                {
                    "path": path,
                    "kind": str(item.get("kind") or artifact_kind(path)),
                    "description": str(item.get("description") or ""),
                    "sensitive": bool(item.get("sensitive", False)),
                    "created": item.get("created"),
                }
            )
    return result


def artifact_kind(path: str) -> str:
    suffix = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if suffix in {"md", "markdown"}:
        return "markdown"
    if suffix == "json":
        return "json"
    if suffix in {"xlsx", "xlsm"}:
        return "xlsx"
    if suffix == "pptx":
        return "pptx"
    if suffix == "drawio":
        return "drawio"
    if suffix == "log":
        return "log"
    return "other"
