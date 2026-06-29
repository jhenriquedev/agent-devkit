"""Canonical capability contract helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.aikit.core.requests import CapabilityRunRequest
from cli.aikit.runtime_paths import ROOT
from cli.aikit.write_policy import write_policy_metadata


def capability_policy(manifest: dict[str, Any]) -> dict[str, Any]:
    return write_policy_metadata(manifest.get("write_policy"))


def normalize_capability_artifacts(value: Any) -> list[dict[str, Any]]:
    artifacts = value if isinstance(value, list) else []
    normalized: list[dict[str, Any]] = []
    for item in artifacts:
        if isinstance(item, str):
            normalized.append(
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
            normalized.append(
                {
                    "path": path,
                    "kind": str(item.get("kind") or artifact_kind(path)),
                    "description": str(item.get("description") or ""),
                    "sensitive": bool(item.get("sensitive", False)),
                    "created": item.get("created"),
                }
            )
    return normalized


def artifact_kind(path: str) -> str:
    suffix = Path(path).suffix.lower().lstrip(".")
    if suffix in {"md", "markdown"}:
        return "markdown"
    if suffix in {"json"}:
        return "json"
    if suffix in {"xlsx", "xlsm"}:
        return "xlsx"
    if suffix in {"pptx"}:
        return "pptx"
    if suffix in {"drawio"}:
        return "drawio"
    if suffix in {"log", "txt"}:
        return "log" if suffix == "log" else "other"
    return "other"


def normalize_capability_definition(
    manifest: dict[str, Any],
    *,
    agent_id: str,
    capability_path: Path | None = None,
) -> dict[str, Any]:
    execution = manifest.get("execution") if isinstance(manifest.get("execution"), dict) else {}
    outputs = manifest.get("outputs") if isinstance(manifest.get("outputs"), dict) else {}
    entrypoint = manifest.get("entrypoint") if isinstance(manifest.get("entrypoint"), dict) else {}
    capability_id = str(manifest.get("id") or "")
    short_id = capability_id.rsplit(".", 1)[-1] if capability_id else ""
    return {
        "id": capability_id,
        "short_id": short_id,
        "agent_id": agent_id,
        "path": str(capability_path.resolve().relative_to(ROOT)) if capability_path else None,
        "entrypoint": entrypoint,
        "inputs": manifest.get("inputs") if isinstance(manifest.get("inputs"), dict) else {},
        "outputs": {
            **outputs,
            "artifacts": normalize_capability_artifacts(outputs.get("artifacts")),
        },
        "requires": manifest.get("requires") if isinstance(manifest.get("requires"), dict) else {},
        "runtime": manifest.get("runtime") if isinstance(manifest.get("runtime"), dict) else {},
        "execution": {
            "modes": list(execution.get("modes") or []),
            "idempotency": execution.get("idempotency"),
            "timeout_seconds": execution.get("timeout_seconds"),
        },
        "policy": capability_policy(manifest),
    }


def capability_request_metadata(request: CapabilityRunRequest) -> dict[str, Any]:
    return {
        "origin": request.origin,
        "request_id": request.request_id,
        "inputs": dict(request.inputs or {}),
        "source_id": request.source_id,
        "dry_run": request.dry_run,
    }


def structured_inputs_to_argv(request: CapabilityRunRequest) -> list[str]:
    args = list(request.capability_args)
    if request.source_id and "--source" not in args and not any(item.startswith("--source=") for item in args):
        args.extend(["--source", request.source_id])
    if request.dry_run and "--dry-run" not in args:
        args.append("--dry-run")
    return args
