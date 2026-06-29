"""Installable workflow MVP for Agent DevKit."""

from __future__ import annotations

from typing import Any

from cli.aikit.tasks import create_task


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


def workflow_list() -> dict[str, Any]:
    return {
        "kind": "workflows",
        "schema_version": WORKFLOW_SCHEMA_VERSION,
        "status": "ok",
        "items": [public_workflow(item) for item in BUILTIN_WORKFLOWS.values()],
    }


def workflow_show(workflow_id: str) -> dict[str, Any]:
    workflow = require_workflow(workflow_id)
    return {"kind": "workflow", "schema_version": WORKFLOW_SCHEMA_VERSION, "status": "ok", "workflow": public_workflow(workflow)}


def workflow_install(workflow_id: str, *, dry_run: bool = True, yes: bool = False) -> dict[str, Any]:
    workflow = require_workflow(workflow_id)
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


def workflow_run(workflow_id: str, *, dry_run: bool = True) -> dict[str, Any]:
    workflow = require_workflow(workflow_id)
    return {
        "kind": "workflow-run",
        "schema_version": WORKFLOW_SCHEMA_VERSION,
        "status": "planned" if dry_run else "blocked",
        "dry_run": dry_run,
        "workflow": public_workflow(workflow),
        "message": "Workflow MVP runs through installed tasks; use workflow install first.",
    }


def require_workflow(workflow_id: str) -> dict[str, Any]:
    workflow = BUILTIN_WORKFLOWS.get(workflow_id or "")
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
    }
