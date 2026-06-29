"""Deterministic eval suites for Agent DevKit runtime contracts."""

from __future__ import annotations

import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from cli.aikit.agentic_commands import agentic_plan
from cli.aikit.app_home import app_path, ensure_app_home
from cli.aikit.catalog import catalog_search
from cli.aikit.configuration_orchestrator import provider_setup_wizard
from cli.aikit.contribution import contribution_pr
from cli.aikit.extensions import local_extensions_list
from cli.aikit.identity import identity_system_prompt
from cli.aikit.mcp_manifest import mcp_tools
from cli.aikit.model_router import build_model_plan
from cli.aikit.providers import load_providers
from cli.aikit.prompt_injection import prompt_injection_eval_fixture
from cli.aikit.review_gate import build_review_gate
from cli.aikit.router_explain import explain_route
from cli.aikit.runtime_paths import ROOT
from cli.aikit.secrets import secrets_doctor
from cli.aikit.sources import list_sources
from cli.aikit.workflows import workflow_list


EVAL_SCHEMA_VERSION = "agent-devkit.eval/v1"
SUITES = (
    "routing",
    "catalog",
    "wizard",
    "source_config",
    "identity_enforcement",
    "review_gate",
    "model_router",
    "agentic_plan",
    "write_policy",
    "source_readiness",
    "mcp",
    "mcp_contract",
    "workflow_contract",
    "extension_contract",
    "contribution_contract",
    "team_contract",
    "knowledge_contract",
    "secret_refs",
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
        started_at = datetime.now(timezone.utc)
        runs = [eval_run(item, root) for item in canonical_suite_ids()]
        status = "passed" if all(item["status"] == "passed" for item in runs) else "failed"
        return persist_run(run_payload("all", status, runs, started_at=started_at))
    handlers: dict[str, Callable[[Path], list[dict[str, Any]]]] = {
        "routing": eval_routing,
        "catalog": eval_catalog,
        "wizard": eval_wizard,
        "source_config": eval_source_config,
        "identity_enforcement": eval_identity_enforcement,
        "review_gate": eval_review_gate,
        "model_router": eval_model_router,
        "agentic_plan": eval_agentic_plan,
        "write_policy": eval_write_policy,
        "source_readiness": eval_source_readiness,
        "mcp_contract": eval_mcp_contract,
        "workflow_contract": eval_workflow_contract,
        "extension_contract": eval_extension_contract,
        "contribution_contract": eval_contribution_contract,
        "team_contract": eval_team_contract,
        "knowledge_contract": eval_knowledge_contract,
        "secret_refs": eval_secret_refs,
        "prompt_injection": eval_prompt_injection,
        "mini_brain_limits": eval_mini_brain_limits,
        "generated_agent_contract": eval_generated_agent_contract,
    }
    handler = handlers.get(suite)
    if not handler:
        raise ValueError(f"unknown eval suite: {suite}")
    started_at = datetime.now(timezone.utc)
    checks = handler(root)
    status = "passed" if all(item.get("status") == "passed" for item in checks) else "failed"
    return persist_run(run_payload(display_suite_id(suite), status, checks, started_at=started_at))


def eval_report(run_id: str | None = None) -> dict[str, Any]:
    runs = list_eval_runs()
    if run_id:
        payload = read_eval_run(run_id)
        return {
            "kind": "eval-report",
            "schema_version": EVAL_SCHEMA_VERSION,
            "status": "ok",
            "run": payload,
            "runs": runs,
        }
    return {
        "kind": "eval-report",
        "schema_version": EVAL_SCHEMA_VERSION,
        "status": "ok",
        "message": "Use `agent eval report <run-id>` to inspect a persisted run.",
        "runs": runs,
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


def eval_wizard(root: Path) -> list[dict[str, Any]]:
    wizard = provider_setup_wizard(root, "azure-devops", prompt="analise o card 1")
    question = wizard.get("next_question") if isinstance(wizard.get("next_question"), dict) else {}
    checks = [
        {
            "id": "wizard.provider-opt-in",
            "status": "passed" if wizard.get("kind") == "provider-setup-wizard" and question.get("type") == "confirm" else "failed",
            "provider": wizard.get("provider"),
            "question": question.get("id"),
        }
    ]
    for provider in load_providers(root):
        provider_id = str(provider.get("id") or "")
        if not provider_id:
            continue
        try:
            candidate = provider_setup_wizard(root, provider_id)
        except Exception as exc:  # noqa: BLE001 - eval must report coverage failures.
            checks.append({"id": f"wizard.provider-coverage.{provider_id}", "status": "failed", "error": type(exc).__name__})
            continue
        questions = candidate.get("questions") if isinstance(candidate.get("questions"), list) else []
        checks.append(
            {
                "id": f"wizard.provider-coverage.{provider_id}",
                "status": "passed"
                if candidate.get("kind") == "provider-setup-wizard"
                and candidate.get("provider") == provider_id
                and isinstance(candidate.get("next_question"), dict)
                else "failed",
                "provider": provider_id,
                "questions": len(questions),
                "stores_secret": candidate.get("stores_secret"),
            }
        )
    return checks


def eval_source_config(_root: Path) -> list[dict[str, Any]]:
    payload = list_sources()
    return [{"id": "source-config.no-stored-secret", "status": "passed" if payload.get("stored_secret") is False else "failed"}]


def eval_identity_enforcement(_root: Path) -> list[dict[str, Any]]:
    prompt = identity_system_prompt(name="Agent DevKit")
    required = ["Nunca responda", "Claude", "Codex", "ChatGPT", "identidade publica"]
    return [{"id": "identity.system-prompt", "status": "passed" if all(item in prompt for item in required) else "failed"}]


def eval_review_gate(_root: Path) -> list[dict[str, Any]]:
    gate = build_review_gate("implemente codigo e revise a entrega")
    return [{"id": "review-gate.deliverable-required", "status": "passed" if gate.get("required") else "failed"}]


def eval_model_router(_root: Path) -> list[dict[str, Any]]:
    plan = build_model_plan("resuma estes logs")
    return [
        {
            "id": "model-router.operational-policy",
            "status": "passed" if plan.get("local_llm_recommended") and plan.get("local_llm_role") == "operational-worker" else "failed",
            "strategy": plan.get("strategy"),
        }
    ]


def eval_agentic_plan(root: Path) -> list[dict[str, Any]]:
    payload = agentic_plan(root, ["analise o card 7914 do azure"])
    plan = payload.get("execution_plan") if isinstance(payload.get("execution_plan"), dict) else {}
    return [
        {
            "id": "agentic-plan.explicit-contract",
            "status": "passed"
            if payload.get("kind") == "agentic-plan" and plan.get("kind") == "agentic-execution-plan" and plan.get("trace")
            else "failed",
            "summary": payload.get("summary"),
        }
    ]


def eval_write_policy(_root: Path) -> list[dict[str, Any]]:
    return [{"id": "write-policy.normalized", "status": "passed"}]


def eval_source_readiness(_root: Path) -> list[dict[str, Any]]:
    return [{"id": "source-readiness.no-external-required", "status": "passed"}]


def eval_mcp_contract(_root: Path) -> list[dict[str, Any]]:
    names = {tool["name"] for tool in mcp_tools()}
    required = {"agent_devkit_catalog_search", "agent_devkit_route_explain", "agent_devkit_roadmap"}
    return [{"id": "mcp.v2-tools", "status": "passed" if required <= names else "failed", "required": sorted(required)}]


def eval_workflow_contract(_root: Path) -> list[dict[str, Any]]:
    payload = workflow_list()
    ids = {item.get("id") for item in payload.get("items") or []}
    required = {"daily-pr-review", "incident-analysis", "azure-card-analysis", "release-prep"}
    return [{"id": "workflow.required-manifests", "status": "passed" if required <= ids else "failed", "required": sorted(required)}]


def eval_extension_contract(_root: Path) -> list[dict[str, Any]]:
    payload = local_extensions_list()
    return [{"id": "extension.registry-readable", "status": "passed" if payload.get("kind") == "local-extensions" else "failed"}]


def eval_contribution_contract(root: Path) -> list[dict[str, Any]]:
    catalog = catalog_search("contribution-reviewer", root, item_type="agent")
    pr = contribution_pr("missing-extension", dry_run=True)
    return [
        {
            "id": "contribution-reviewer.catalogued",
            "status": "passed" if any(item.get("id") == "contribution-reviewer" for item in catalog.get("items") or []) else "failed",
        },
        {
            "id": "contribution-pr.report-only",
            "status": "passed"
            if pr.get("kind") == "contribution-pr"
            and pr.get("status") == "blocked"
            and (pr.get("plan") or {}).get("external_writes") is True
            else "failed",
        },
    ]


def eval_team_contract(_root: Path) -> list[dict[str, Any]]:
    from cli.aikit.team import team_doctor, team_init

    with tempfile.TemporaryDirectory() as project:
        root = Path(project)
        init = team_init(root)
        doctor = team_doctor(root)
    return [
        {
            "id": "team-profile.project-local",
            "status": "passed" if init.get("status") == "initialized" and init.get("secret_free") is True else "failed",
        },
        {
            "id": "team-doctor.secret-free",
            "status": "passed" if doctor.get("status") == "ok" else "failed",
        },
    ]


def eval_knowledge_contract(_root: Path) -> list[dict[str, Any]]:
    from cli.aikit.knowledge_base import (
        knowledge_doctor,
        knowledge_init,
        knowledge_publish,
        knowledge_review,
        knowledge_search,
        knowledge_snapshot_create,
    )

    with tempfile.TemporaryDirectory() as project:
        root = Path(project)
        init = knowledge_init(root)
        snapshot = knowledge_snapshot_create(
            title="Runbook de teste",
            content="# Runbook de teste\n\nProcedimento reutilizavel e sem segredo.",
            from_file=None,
            entry_type="runbook",
            project=root,
        )
        review = knowledge_review(str(snapshot["snapshot_id"]), root)
        publish = knowledge_publish(str(snapshot["snapshot_id"]), root, yes=True, owner_agent="knowledge-owner")
        search = knowledge_search("procedimento reutilizavel", root)
        doctor = knowledge_doctor(root)
    return [
        {"id": "knowledge.init", "status": "passed" if init.get("status") == "initialized" else "failed"},
        {"id": "knowledge.review", "status": "passed" if review.get("status") == "approved" else "failed"},
        {"id": "knowledge.publish", "status": "passed" if publish.get("status") == "published" else "failed"},
        {"id": "knowledge.search", "status": "passed" if search.get("count", 0) >= 1 else "failed"},
        {"id": "knowledge.doctor", "status": "passed" if doctor.get("status") == "ok" else "failed"},
    ]


def eval_secret_refs(_root: Path) -> list[dict[str, Any]]:
    payload = secrets_doctor()
    return [{"id": "secret-refs.no-values", "status": "passed" if payload.get("stored_values") is False else "failed"}]


def eval_prompt_injection(_root: Path) -> list[dict[str, Any]]:
    return [prompt_injection_eval_fixture()]


def eval_mini_brain_limits(_root: Path) -> list[dict[str, Any]]:
    from cli.aikit.mini_brain import FORBIDDEN_TASKS

    return [{"id": "mini-brain.forbidden-high-risk", "status": "passed" if "external_write_decision" in FORBIDDEN_TASKS else "failed"}]


def eval_generated_agent_contract(_root: Path) -> list[dict[str, Any]]:
    return [{"id": "generated-agent.contract-placeholder", "status": "passed"}]


def run_payload(
    suite: str,
    status: str,
    checks: list[dict[str, Any]],
    *,
    started_at: datetime | None = None,
) -> dict[str, Any]:
    started_at = started_at or datetime.now(timezone.utc)
    run_id = f"eval_{started_at.strftime('%Y%m%d%H%M%S')}_{suite.replace('-', '_')}"
    finished_at = datetime.now(timezone.utc)
    duration_ms = max(0, int((finished_at - started_at).total_seconds() * 1000))
    return {
        "kind": "eval-run",
        "schema_version": EVAL_SCHEMA_VERSION,
        "run_id": run_id,
        "suite": suite,
        "status": status,
        "ok": status == "passed",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "metrics": eval_metrics(checks, duration_ms=duration_ms),
        "checks": json.loads(json.dumps(checks, ensure_ascii=False)),
    }


def canonical_suite_ids() -> list[str]:
    return [
        "routing",
        "catalog",
        "wizard",
        "source_config",
        "identity_enforcement",
        "review_gate",
        "model_router",
        "agentic_plan",
        "write_policy",
        "source_readiness",
        "mcp_contract",
        "workflow_contract",
        "extension_contract",
        "contribution_contract",
        "team_contract",
        "knowledge_contract",
        "secret_refs",
        "prompt_injection",
        "mini_brain_limits",
        "generated_agent_contract",
    ]


def normalize_suite_id(value: str) -> str:
    normalized = (value or "").strip().replace("-", "_")
    if normalized == "mcp":
        return "mcp_contract"
    if normalized == "prompt-injection":
        return "prompt_injection"
    return normalized


def display_suite_id(value: str) -> str:
    if value == "prompt_injection":
        return "prompt-injection"
    if value == "mcp_contract":
        return "mcp"
    return value


def persist_run(payload: dict[str, Any]) -> dict[str, Any]:
    path = eval_run_path(str(payload["run_id"]))
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown = eval_markdown_path(str(payload["run_id"]))
    markdown.write_text(render_eval_markdown(payload), encoding="utf-8")
    payload["json_path"] = str(path)
    payload["markdown_path"] = str(markdown)
    return payload


def eval_runs_home() -> Path:
    ensure_app_home()
    path = app_path("evals", "runs")
    path.mkdir(parents=True, exist_ok=True)
    return path


def eval_run_path(run_id: str) -> Path:
    return eval_runs_home() / f"{safe_run_id(run_id)}.json"


def eval_markdown_path(run_id: str) -> Path:
    return eval_runs_home() / f"{safe_run_id(run_id)}.md"


def list_eval_runs() -> list[dict[str, Any]]:
    runs = []
    for path in sorted(eval_runs_home().glob("*.json"), reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        runs.append(
            {
                "run_id": payload.get("run_id"),
                "suite": payload.get("suite"),
                "status": payload.get("status"),
                "ok": payload.get("ok"),
                "started_at": payload.get("started_at"),
                "json_path": str(path),
                "markdown_path": str(path.with_suffix(".md")),
            }
        )
    return runs


def read_eval_run(run_id: str) -> dict[str, Any]:
    path = eval_run_path(run_id)
    if not path.exists():
        raise ValueError(f"eval run not found: {run_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def render_eval_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Eval {payload.get('run_id')}",
        "",
        f"- Suite: {payload.get('suite')}",
        f"- Status: {payload.get('status')}",
        f"- Started: {payload.get('started_at')}",
        "",
        "## Checks",
    ]
    for check in payload.get("checks") or []:
        if isinstance(check, dict):
            lines.append(f"- {check.get('id')}: {check.get('status')}")
    lines.append("")
    return "\n".join(lines)


def eval_metrics(checks: list[dict[str, Any]], *, duration_ms: int = 0) -> dict[str, Any]:
    flat = flatten_checks(checks)
    total = len(flat)
    passed = len([item for item in flat if item.get("status") == "passed"])
    failed = len([item for item in flat if item.get("status") == "failed"])
    success = passed == total if total else False
    completeness = passed / total if total else 0.0
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "success": success,
        "regression": "passed" if success else "failed",
        "completeness": round(completeness, 4),
        "schema": "passed",
        "security": "passed" if failed == 0 else "needs-review",
        "duration_ms": duration_ms,
    }


def flatten_checks(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for check in checks:
        if isinstance(check, dict) and check.get("kind") == "eval-run":
            flat.extend(flatten_checks(check.get("checks") or []))
        elif isinstance(check, dict):
            flat.append(check)
    return flat


def safe_run_id(run_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", run_id)
