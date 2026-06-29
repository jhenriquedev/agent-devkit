"""Installable workflow MVP for Agent DevKit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.aikit.runtime_paths import ROOT
from cli.aikit.tasks import create_task, load_tasks, run_task


WORKFLOW_SCHEMA_VERSION = "agent-devkit.workflows/v1"


BUILTIN_WORKFLOWS: dict[str, dict[str, Any]] = {
    "daily-pr-review": {
        "id": "daily-pr-review",
        "title": "Daily PR review",
        "description": "Create a local scheduled prompt to review pending pull requests.",
        "schedule": {"type": "cron", "cron": "0 9 * * 1-5"},
        "task": {
            "title": "Daily PR review",
            "prompt": "Revise as PRs que aguardam minha revisao hoje.",
            "action": {"type": "prompt", "prompt": "Revise as PRs que aguardam minha revisao hoje.", "external_writes": False},
            "permissions": {"mode": "report-only"},
            "notifications": [{"type": "desktop", "events": ["task.completed", "task.blocked"]}],
        },
        "write_policy": "local_config_write",
    }
}


def workflow_list(root: Path | None = None) -> dict[str, Any]:
    workflows = load_workflows(root or ROOT)
    return {
        "kind": "workflows",
        "schema_version": WORKFLOW_SCHEMA_VERSION,
        "status": "ok",
        "items": [public_workflow(item) for item in workflows.values()],
    }


def workflow_show(workflow_id: str, root: Path | None = None) -> dict[str, Any]:
    workflow = require_workflow(workflow_id, root=root)
    return {"kind": "workflow", "schema_version": WORKFLOW_SCHEMA_VERSION, "status": "ok", "workflow": public_workflow(workflow)}


def workflow_install(workflow_id: str, *, dry_run: bool = True, yes: bool = False, root: Path | None = None) -> dict[str, Any]:
    workflow = require_workflow(workflow_id, root=root)
    mode = "dry-run" if dry_run or not yes else "apply"
    task = workflow["task"]
    plan = {
        "task": {
            "id": workflow["id"],
            "title": task["title"],
            "schedule": workflow["schedule"],
            "permissions": task["permissions"],
            "notifications": task["notifications"],
        },
        "writes": ["local task registry"],
        "stores_secret": False,
    }
    if mode == "dry-run":
        return {
            "kind": "workflow-install",
            "schema_version": WORKFLOW_SCHEMA_VERSION,
            "status": "planned",
            "mode": "dry-run",
            "workflow": public_workflow(workflow),
            "plan": plan,
        }
    created = create_task(
        task_id=workflow["id"],
        title=task["title"],
        prompt=task["prompt"],
        schedule=workflow["schedule"],
        action=task["action"],
        permissions=task["permissions"],
        notifications=task["notifications"],
    )
    return {
        "kind": "workflow-install",
        "schema_version": WORKFLOW_SCHEMA_VERSION,
        "status": "installed",
        "mode": "apply",
        "workflow": public_workflow(workflow),
        "task": created.get("task"),
    }


def workflow_run(workflow_id: str, *, dry_run: bool = True, root: Path | None = None) -> dict[str, Any]:
    workflow = require_workflow(workflow_id, root=root)
    task = workflow["task"]
    plan = {
        "task": {
            "id": workflow["id"],
            "title": task["title"],
            "schedule": workflow["schedule"],
            "action": task["action"],
            "permissions": task["permissions"],
            "notifications": task["notifications"],
        },
        "writes": ["local task registry", "task history"] if not dry_run else [],
        "stores_secret": False,
    }
    if dry_run:
        return {
            "kind": "workflow-run",
            "schema_version": WORKFLOW_SCHEMA_VERSION,
            "status": "planned",
            "dry_run": True,
            "workflow": public_workflow(workflow),
            "plan": plan,
            "next_steps": [f"Run `agent workflow run {workflow['id']} --yes` to execute through the local task runtime."],
        }
    installed = ensure_workflow_task(workflow)
    task_run = run_task(workflow["id"], dry_run=False, origin="workflow")
    return {
        "kind": "workflow-run",
        "schema_version": WORKFLOW_SCHEMA_VERSION,
        "status": task_run.get("status") or "failed",
        "ok": task_run.get("ok") is True,
        "dry_run": False,
        "workflow": public_workflow(workflow),
        "task_installed": installed,
        "task_run": task_run,
        "exit_code": task_run.get("exit_code"),
    }


def ensure_workflow_task(workflow: dict[str, Any]) -> bool:
    task_id = workflow["id"]
    data = load_tasks()
    for item in data.get("tasks") or []:
        if isinstance(item, dict) and item.get("id") == task_id:
            return False
    task = workflow["task"]
    create_task(
        task_id=task_id,
        title=task["title"],
        prompt=task["prompt"],
        schedule=workflow["schedule"],
        action=task["action"],
        permissions=task["permissions"],
        notifications=task["notifications"],
    )
    return True


def require_workflow(workflow_id: str, root: Path | None = None) -> dict[str, Any]:
    workflow = load_workflows(root or ROOT).get(workflow_id or "")
    if not workflow:
        raise ValueError(f"workflow not found: {workflow_id}")
    return workflow


def public_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": workflow["id"],
        "title": workflow["title"],
        "description": workflow["description"],
        "schedule": workflow["schedule"],
        "write_policy": workflow["write_policy"],
        "stores_secret": False,
        "providers_required": workflow.get("providers") or workflow.get("providers_required") or [],
        "permissions": workflow.get("permissions") or {},
        "outputs": workflow.get("outputs") or [],
        "risks": workflow.get("risks") or [],
        "examples": workflow.get("examples") or [],
        "path": workflow.get("path"),
    }


def load_workflows(root: Path) -> dict[str, dict[str, Any]]:
    workflows = dict(BUILTIN_WORKFLOWS)
    workflows_dir = root / "workflows"
    if not workflows_dir.exists():
        return workflows
    for manifest in sorted(workflows_dir.glob("*/workflow.yaml")):
        item = load_workflow_manifest(manifest)
        if item:
            workflows[item["id"]] = item
    return workflows


def load_workflow_manifest(path: Path) -> dict[str, Any] | None:
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not data.get("id"):
        return None
    workflow = dict(data)
    workflow.setdefault("title", str(workflow["id"]))
    workflow.setdefault("description", "")
    workflow.setdefault("schedule", {"type": "manual"})
    workflow.setdefault("permissions", {"mode": "report-only"})
    workflow.setdefault("write_policy", "local_config_write")
    workflow.setdefault("task", default_task(workflow))
    workflow["path"] = str(path)
    return workflow


def default_task(workflow: dict[str, Any]) -> dict[str, Any]:
    prompt = str(workflow.get("description") or workflow.get("title") or workflow.get("id"))
    return {
        "title": workflow.get("title") or workflow.get("id"),
        "prompt": prompt,
        "action": {"type": "prompt", "prompt": prompt, "external_writes": False},
        "permissions": workflow.get("permissions") or {"mode": "report-only"},
        "notifications": [{"type": "desktop", "events": ["task.completed", "task.blocked"]}],
    }
