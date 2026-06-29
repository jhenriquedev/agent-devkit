"""Doctor and diagnostics payload builder for the CLI."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from cli.aikit.capability_runtime import list_agents, list_all_capabilities
from cli.aikit.catalog import catalog_list
from cli.aikit.diagnostics import build_diagnostics
from cli.aikit.eval import eval_list
from cli.aikit.extensions import local_extensions_list
from cli.aikit.knowledge_base import knowledge_doctor
from cli.aikit.lock import lock_status
from cli.aikit.local_llm import local_llm_doctor
from cli.aikit.runtime_paths import AGENTS_DIR, ROOT
from cli.aikit.secrets import secrets_doctor
from cli.aikit.specialist_readiness import specialist_readiness
from cli.aikit.team import team_status
from cli.aikit.workflows import workflow_list


def doctor(project: str | None = None, home: str | None = None, scope: str = "auto") -> dict[str, Any]:
    agents = list_agents()
    capabilities = list_all_capabilities()
    declared_runners = sum(1 for item in capabilities if item.get("has_runner"))
    workflows = sum(1 for item in capabilities if item.get("has_workflow"))
    decision_rules = sum(1 for item in capabilities if item.get("has_decision_rules"))
    validator = ROOT / "scripts" / "validate-repo.py"
    errors: list[str] = []
    warnings: list[str] = []

    if not ROOT.exists():
        errors.append(f"root not found: {ROOT}")
    if not AGENTS_DIR.is_dir():
        errors.append(f"agents directory not found: {AGENTS_DIR}")
    if not validator.exists():
        warnings.append("scripts/validate-repo.py not found")
    project_path = doctor_project_path(project, scope)
    home_path = Path(home) if home else None
    locks = lock_status(project_path, home_path)
    if project and locks["status"] == "diverged":
        warnings.append("lock divergence between global runtime.lock and project ai-devkit.lock")
    checks = {
        "root_exists": ROOT.exists(),
        "agents_dir_exists": AGENTS_DIR.is_dir(),
        "validator_exists": validator.exists(),
        "agent_command_exists": (ROOT / "agent").exists(),
        "aikit_command_exists": (ROOT / "aikit").exists(),
        "ai_devkit_command_exists": (ROOT / "ai-devkit").exists(),
        "agent_on_path": shutil.which("agent") is not None,
    }
    diagnostics = build_diagnostics(
        ROOT,
        project=project_path,
        home=home_path,
        runtime_checks=checks,
        runtime_status="ok" if not errors else "error",
        locks=locks,
    )
    operational = operational_diagnostics(project_path)

    return {
        "kind": "doctor",
        "status": "ok" if not errors else "error",
        "scope": scope,
        "root": str(ROOT),
        "summary": {
            "agents": len(agents),
            "capabilities": len(capabilities),
            "declared_runners": declared_runners,
            "workflows": workflows,
            "decision_rules": decision_rules,
        },
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "locks": locks,
        "diagnostics": diagnostics,
        "operational": operational,
    }


def doctor_project_path(project: str | None, scope: str) -> Path | None:
    if project:
        return Path(project)
    if scope == "project":
        return Path.cwd()
    return None


def operational_diagnostics(project_path: Path | None = None) -> dict[str, Any]:
    return {
        "catalog": summarize_call(lambda: catalog_list(ROOT), count_key="count"),
        "evals": summarize_call(lambda: eval_list(), count_path=("suites",)),
        "workflows": summarize_call(lambda: workflow_list(ROOT), count_path=("items",)),
        "secret_refs": summarize_secret_refs(),
        "local_llm": summarize_local_llm(),
        "specialists": summarize_specialists(),
        "extensions": summarize_call(lambda: local_extensions_list(), count_path=("items",)),
        "team": summarize_call(lambda: team_status(project_path or Path.cwd())),
        "knowledge": summarize_call(lambda: knowledge_doctor(project_path or Path.cwd())),
    }


def summarize_call(factory, *, count_key: str | None = None, count_path: tuple[str, ...] | None = None) -> dict[str, Any]:
    try:
        payload = factory()
    except Exception as exc:  # noqa: BLE001 - doctor must report subsystem failures.
        return {"status": "error", "error": type(exc).__name__}
    count = payload.get(count_key) if count_key else None
    if count is None and count_path:
        value: Any = payload
        for key in count_path:
            value = value.get(key) if isinstance(value, dict) else None
        count = len(value) if isinstance(value, list) else None
    return {"status": payload.get("status", "ok"), "kind": payload.get("kind"), "count": count}


def summarize_secret_refs() -> dict[str, Any]:
    try:
        payload = secrets_doctor()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": type(exc).__name__}
    return {
        "status": payload.get("status"),
        "kind": payload.get("kind"),
        "references": len(payload.get("references") or []),
        "stored_values": payload.get("stored_values") is True,
    }


def summarize_local_llm() -> dict[str, Any]:
    try:
        payload = local_llm_doctor()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": type(exc).__name__}
    mini = payload.get("mini_brain") if isinstance(payload.get("mini_brain"), dict) else {}
    ollama = payload.get("ollama") if isinstance(payload.get("ollama"), dict) else {}
    return {
        "status": payload.get("status"),
        "kind": payload.get("kind"),
        "ollama": ollama.get("status"),
        "mini_brain": mini.get("status"),
        "enabled": mini.get("enabled") is True,
    }


def summarize_specialists() -> dict[str, Any]:
    try:
        payload = specialist_readiness(ROOT)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": type(exc).__name__}
    return {
        "status": payload.get("status"),
        "kind": payload.get("kind"),
        "agents_total": payload.get("agents_total"),
        "agents_with_provider_requirements": payload.get("agents_with_provider_requirements"),
        "ready_agents": payload.get("ready_agents"),
        "partial_agents": payload.get("partial_agents"),
        "needs_setup_agents": payload.get("needs_setup_agents"),
        "missing_providers": payload.get("missing_providers") or [],
    }
