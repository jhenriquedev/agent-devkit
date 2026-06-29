"""Doctor and diagnostics payload builder for the CLI."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from cli.aikit.capability_runtime import list_agents, list_all_capabilities
from cli.aikit.diagnostics import build_diagnostics
from cli.aikit.lock import lock_status
from cli.aikit.runtime_paths import AGENTS_DIR, ROOT


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
    }


def doctor_project_path(project: str | None, scope: str) -> Path | None:
    if project:
        return Path(project)
    if scope == "project":
        return Path.cwd()
    return None
