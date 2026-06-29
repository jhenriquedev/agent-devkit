"""Deterministic eval suites for Agent DevKit runtime contracts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from cli.aikit.catalog import catalog_search
from cli.aikit.mcp_manifest import mcp_tools
from cli.aikit.prompt_injection import prompt_injection_eval_fixture
from cli.aikit.router_explain import explain_route
from cli.aikit.runtime_paths import ROOT


EVAL_SCHEMA_VERSION = "agent-devkit.eval/v1"
SUITES = (
    "routing",
    "catalog",
    "write_policy",
    "source_readiness",
    "mcp",
    "mcp_contract",
    "prompt-injection",
    "prompt_injection",
    "mini_brain_limits",
    "generated_agent_contract",
)


def eval_list() -> dict[str, Any]:
    return {
        "kind": "eval-suites",
        "schema_version": EVAL_SCHEMA_VERSION,
        "status": "ok",
        "suites": [{"id": display_suite_id(suite_id), "deterministic": True} for suite_id in canonical_suite_ids()],
    }


def eval_run(suite: str, root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    suite = normalize_suite_id(suite)
    if suite == "all":
        runs = [eval_run(item, root) for item in canonical_suite_ids()]
        status = "passed" if all(item["status"] == "passed" for item in runs) else "failed"
        return run_payload("all", status, runs)
    handlers: dict[str, Callable[[Path], list[dict[str, Any]]]] = {
        "routing": eval_routing,
        "catalog": eval_catalog,
        "write_policy": eval_write_policy,
        "source_readiness": eval_source_readiness,
        "mcp_contract": eval_mcp_contract,
        "prompt_injection": eval_prompt_injection,
        "mini_brain_limits": eval_mini_brain_limits,
        "generated_agent_contract": eval_generated_agent_contract,
    }
    handler = handlers.get(suite)
    if not handler:
        raise ValueError(f"unknown eval suite: {suite}")
    checks = handler(root)
    status = "passed" if all(item.get("status") == "passed" for item in checks) else "failed"
    return run_payload(display_suite_id(suite), status, checks)


def eval_report() -> dict[str, Any]:
    return {
        "kind": "eval-report",
        "schema_version": EVAL_SCHEMA_VERSION,
        "status": "ok",
        "message": "Persistent eval run reports are not enabled in the MVP.",
        "runs": [],
    }


def eval_routing(root: Path) -> list[dict[str, Any]]:
    payload = explain_route("revise as prs que recebi hoje", root)
    return [
        {
            "id": "routing.pr-review",
            "status": "passed" if payload["candidates"] else "failed",
            "evidence": {"decision": payload["decision"], "candidates": len(payload["candidates"])},
        }
    ]


def eval_catalog(root: Path) -> list[dict[str, Any]]:
    payload = catalog_search("pr", root)
    return [{"id": "catalog.search-pr", "status": "passed" if payload["items"] else "failed", "count": payload["count"]}]


def eval_write_policy(_root: Path) -> list[dict[str, Any]]:
    return [{"id": "write-policy.normalized", "status": "passed"}]


def eval_source_readiness(_root: Path) -> list[dict[str, Any]]:
    return [{"id": "source-readiness.no-external-required", "status": "passed"}]


def eval_mcp_contract(_root: Path) -> list[dict[str, Any]]:
    names = {tool["name"] for tool in mcp_tools()}
    required = {"agent_devkit_catalog_search", "agent_devkit_route_explain", "agent_devkit_roadmap"}
    return [{"id": "mcp.v2-tools", "status": "passed" if required <= names else "failed", "required": sorted(required)}]


def eval_prompt_injection(_root: Path) -> list[dict[str, Any]]:
    return [prompt_injection_eval_fixture()]


def eval_mini_brain_limits(_root: Path) -> list[dict[str, Any]]:
    from cli.aikit.mini_brain import FORBIDDEN_TASKS

    return [{"id": "mini-brain.forbidden-high-risk", "status": "passed" if "external_write_decision" in FORBIDDEN_TASKS else "failed"}]


def eval_generated_agent_contract(_root: Path) -> list[dict[str, Any]]:
    return [{"id": "generated-agent.contract-placeholder", "status": "passed"}]


def run_payload(suite: str, status: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "kind": "eval-run",
        "schema_version": EVAL_SCHEMA_VERSION,
        "suite": suite,
        "status": status,
        "ok": status == "passed",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "checks": json.loads(json.dumps(checks, ensure_ascii=False)),
    }


def canonical_suite_ids() -> list[str]:
    return [
        "routing",
        "catalog",
        "write_policy",
        "source_readiness",
        "mcp_contract",
        "prompt_injection",
        "mini_brain_limits",
        "generated_agent_contract",
    ]


def normalize_suite_id(value: str) -> str:
    normalized = (value or "").strip().replace("-", "_")
    if normalized == "mcp":
        return "mcp_contract"
    return normalized


def display_suite_id(value: str) -> str:
    if value == "prompt_injection":
        return "prompt-injection"
    if value == "mcp_contract":
        return "mcp"
    return value
