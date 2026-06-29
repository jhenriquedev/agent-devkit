"""Public roadmap payloads for Agent DevKit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.aikit.architecture import architecture_contract
from cli.aikit.roadmap import implementation_phases, problem_phase_map, recommended_initial_order
from cli.aikit.runtime_paths import ROOT


ROADMAP_SCHEMA_VERSION = "agent-devkit.roadmap/v1"
DEFAULT_PRETERIDO_PROBLEMS = {24, 25, 26}


def roadmap_payload(root: Path | None = None, *, phase: int | None = None, problem: int | None = None) -> dict[str, Any]:
    root = root or ROOT
    preteridos = preterido_problem_numbers(root)
    phases = [filter_phase(item, preteridos) for item in implementation_phases()]
    if phase is not None:
        phases = [item for item in phases if item["number"] == phase]
    if problem is not None:
        phases = [item for item in phases if problem in item["problems"]]
    active = sorted({int(item) for phase_item in phases for item in phase_item.get("problems", [])})
    active_problem_set = set(active)
    out_of_scope_problem = problem if problem is not None and problem in preteridos else None
    return {
        "kind": "roadmap",
        "schema_version": ROADMAP_SCHEMA_VERSION,
        "status": "ok",
        "version_scope": "v0.3.0",
        "source": "cli.aikit.roadmap",
        "active_problems": active,
        "preteridos": sorted(preteridos),
        "recommended_initial_order": [
            item for item in recommended_initial_order() if item not in preteridos
        ],
        "phases": phases,
        "problem_phase_map": {
            str(key): value
            for key, value in problem_phase_map().items()
            if int(key) in active_problem_set
        },
        "out_of_scope_problem": out_of_scope_problem,
        "architecture": {
            "schema_version": architecture_contract(root).get("schema_version"),
            "principal_agent": architecture_contract(root).get("principal_agent"),
        },
    }


def preterido_problem_numbers(root: Path) -> set[int]:
    result = set(DEFAULT_PRETERIDO_PROBLEMS)
    problems_dir = root / "docs" / "problems"
    if not problems_dir.exists():
        return result
    for path in problems_dir.glob("*_preterido.md"):
        prefix = path.name.split("_", 1)[0]
        if prefix.isdigit():
            result.add(int(prefix))
    return result


def filter_phase(phase: dict[str, Any], preteridos: set[int]) -> dict[str, Any]:
    result = dict(phase)
    result["problems"] = [int(item) for item in phase.get("problems", []) if int(item) not in preteridos]
    result["out_of_scope_problems"] = [int(item) for item in phase.get("problems", []) if int(item) in preteridos]
    result["status"] = "active" if result["problems"] else "empty-after-scope-filter"
    return result
