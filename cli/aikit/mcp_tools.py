"""MCP tool adapters over the Agent DevKit core runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from cli.aikit.audit import redact_value, try_record_audit
from cli.aikit.agentic_commands import agentic_plan
from cli.aikit.catalog import catalog_list, catalog_search, catalog_show
from cli.aikit.core.requests import CapabilityRunRequest
from cli.aikit.core.runtime import (
    inspect_capability_request,
    list_agent_modules,
    list_capability_modules,
    run_capability_request,
)
from cli.aikit.doctor_runtime import doctor
from cli.aikit.eval import eval_list, eval_run
from cli.aikit.errors import DevKitError
from cli.aikit.local_artifacts import (
    local_agent_list,
    local_agent_create,
    local_agent_show,
    local_agent_validate,
    local_automation_create,
    local_automation_enable,
    local_automation_list,
    local_automation_show,
    local_automation_validate,
    script_create,
    script_list,
    script_run,
    skill_create,
    skill_list,
    skill_show,
)
from cli.aikit.local_llm import local_llm_doctor, local_llm_list, local_llm_models
from cli.aikit.knowledge_base import (
    knowledge_base_create,
    knowledge_base_join,
    knowledge_base_rotate_token,
    knowledge_base_status,
    knowledge_base_tokens,
    knowledge_curate,
    knowledge_doctor,
    knowledge_index,
    knowledge_init,
    knowledge_publish,
    knowledge_review,
    knowledge_review_list,
    knowledge_search,
    knowledge_sync,
    knowledge_snapshot_create,
    knowledge_snapshot_list,
    knowledge_snapshot_score,
    knowledge_snapshot_show,
    knowledge_snapshot_submit,
)
from cli.aikit.memory import (
    create_memory_backup,
    delete_memory_backup,
    list_memory_backups,
    memory_path_payload,
    reset_memory,
    restore_memory_backup,
    show_memory,
)
from cli.aikit.mcp_manifest import mcp_tools
from cli.aikit.notifications import (
    format_notification_event,
    list_notification_channels,
    list_notification_events,
    notification_doctor,
)
from cli.aikit.onboarding import onboarding_status
from cli.aikit.orchestrator import build_execution_plan
from cli.aikit.personality import load_personality, reset_personality, update_personality
from cli.aikit.roadmap_cli import roadmap_payload
from cli.aikit.router_explain import explain_route
from cli.aikit.runtime_paths import ROOT
from cli.aikit.secrets import secrets_doctor
from cli.aikit.shared_memory import (
    shared_memory_create,
    shared_memory_list,
    shared_memory_publish,
    shared_memory_read,
    shared_memory_review,
    shared_memory_status,
    shared_memory_submit,
)
from cli.aikit.sources import SourceRegistryError, list_sources, source_status
from cli.aikit.tasks import list_tasks, run_task, scheduler_run_once, show_task
from cli.aikit.team import (
    team_doctor,
    team_init,
    team_onboard,
    team_profile_export,
    team_profile_import,
    team_profile_list,
    team_profile_show,
    team_status,
)
from cli.aikit.workflows import workflow_list, workflow_run, workflow_show
from cli.aikit.wizard_state import WizardStateError, answer_wizard, show_wizard


class McpToolError(ValueError):
    """Raised when a MCP tool call is malformed or unknown."""


def call_mcp_tool(name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    args = arguments or {}
    if not isinstance(args, dict):
        raise McpToolError("MCP tool arguments must be an object")
    handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
        "agent_devkit_agents_list": tool_agents_list,
        "agent_devkit_capabilities_list": tool_capabilities_list,
        "agent_devkit_capability_inspect": tool_capability_inspect,
        "agent_devkit_capability_run": tool_capability_run,
        "agent_devkit_doctor": tool_doctor,
        "agent_devkit_onboarding_status": tool_onboarding_status,
        "agent_devkit_memory_show": tool_memory_show,
        "agent_devkit_memory_path": tool_memory_path,
        "agent_devkit_memory_reset": tool_memory_reset,
        "agent_devkit_memory_backup_create": tool_memory_backup_create,
        "agent_devkit_memory_backup_list": tool_memory_backup_list,
        "agent_devkit_memory_backup_restore": tool_memory_backup_restore,
        "agent_devkit_memory_backup_delete": tool_memory_backup_delete,
        "agent_devkit_shared_memory_list": tool_shared_memory_list,
        "agent_devkit_shared_memory_status": tool_shared_memory_status,
        "agent_devkit_shared_memory_create": tool_shared_memory_create,
        "agent_devkit_shared_memory_read": tool_shared_memory_read,
        "agent_devkit_shared_memory_submit": tool_shared_memory_submit,
        "agent_devkit_shared_memory_review": tool_shared_memory_review,
        "agent_devkit_shared_memory_publish": tool_shared_memory_publish,
        "agent_devkit_personality_show": tool_personality_show,
        "agent_devkit_personality_update": tool_personality_update,
        "agent_devkit_personality_reset": tool_personality_reset,
        "agent_devkit_task_list": tool_task_list,
        "agent_devkit_task_show": tool_task_show,
        "agent_devkit_task_run_dry_run": tool_task_run_dry_run,
        "agent_devkit_scheduler_run_once_dry_run": tool_scheduler_run_once_dry_run,
        "agent_devkit_notifications_doctor": tool_notifications_doctor,
        "agent_devkit_notifications_list_events": tool_notifications_list_events,
        "agent_devkit_notifications_list_channels": tool_notifications_list_channels,
        "agent_devkit_notifications_format": tool_notifications_format,
        "agent_devkit_catalog_list": tool_catalog_list,
        "agent_devkit_catalog_search": tool_catalog_search,
        "agent_devkit_catalog_show": tool_catalog_show,
        "agent_devkit_route_explain": tool_route_explain,
        "agent_devkit_agent_prompt_dry_run": tool_agent_prompt_dry_run,
        "agent_devkit_agentic_plan": tool_agentic_plan,
        "agent_devkit_eval_list": tool_eval_list,
        "agent_devkit_eval_run": tool_eval_run,
        "agent_devkit_secrets_doctor": tool_secrets_doctor,
        "agent_devkit_workflow_list": tool_workflow_list,
        "agent_devkit_workflow_show": tool_workflow_show,
        "agent_devkit_workflow_run_dry_run": tool_workflow_run_dry_run,
        "agent_devkit_local_llm_list": tool_local_llm_list,
        "agent_devkit_local_llm_doctor": tool_local_llm_doctor,
        "agent_devkit_local_llm_models": tool_local_llm_models,
        "agent_devkit_local_artifacts_list": tool_local_artifacts_list,
        "agent_devkit_local_skill_create": tool_local_skill_create,
        "agent_devkit_local_skill_list": tool_local_skill_list,
        "agent_devkit_local_skill_show": tool_local_skill_show,
        "agent_devkit_local_script_create": tool_local_script_create,
        "agent_devkit_local_script_list": tool_local_script_list,
        "agent_devkit_local_script_run_dry_run": tool_local_script_run_dry_run,
        "agent_devkit_local_agent_create": tool_local_agent_create,
        "agent_devkit_local_agent_list": tool_local_agent_list,
        "agent_devkit_local_agent_show": tool_local_agent_show,
        "agent_devkit_local_agent_validate": tool_local_agent_validate,
        "agent_devkit_local_automation_create": tool_local_automation_create,
        "agent_devkit_local_automation_list": tool_local_automation_list,
        "agent_devkit_local_automation_show": tool_local_automation_show,
        "agent_devkit_local_automation_enable": tool_local_automation_enable,
        "agent_devkit_local_automation_disable": tool_local_automation_disable,
        "agent_devkit_local_automation_validate": tool_local_automation_validate,
        "agent_devkit_team_status": tool_team_status,
        "agent_devkit_team_doctor": tool_team_doctor,
        "agent_devkit_team_init": tool_team_init,
        "agent_devkit_team_onboard": tool_team_onboard,
        "agent_devkit_team_profile_list": tool_team_profile_list,
        "agent_devkit_team_profile_show": tool_team_profile_show,
        "agent_devkit_team_profile_export": tool_team_profile_export,
        "agent_devkit_team_profile_import": tool_team_profile_import,
        "agent_devkit_knowledge_doctor": tool_knowledge_doctor,
        "agent_devkit_knowledge_init": tool_knowledge_init,
        "agent_devkit_knowledge_index": tool_knowledge_index,
        "agent_devkit_knowledge_search": tool_knowledge_search,
        "agent_devkit_knowledge_curate": tool_knowledge_curate,
        "agent_devkit_knowledge_sync": tool_knowledge_sync,
        "agent_devkit_knowledge_snapshot_create": tool_knowledge_snapshot_create,
        "agent_devkit_knowledge_snapshot_list": tool_knowledge_snapshot_list,
        "agent_devkit_knowledge_snapshot_show": tool_knowledge_snapshot_show,
        "agent_devkit_knowledge_snapshot_score": tool_knowledge_snapshot_score,
        "agent_devkit_knowledge_snapshot_submit": tool_knowledge_snapshot_submit,
        "agent_devkit_knowledge_review_list": tool_knowledge_review_list,
        "agent_devkit_knowledge_review": tool_knowledge_review,
        "agent_devkit_knowledge_publish": tool_knowledge_publish,
        "agent_devkit_knowledge_base_create": tool_knowledge_base_create,
        "agent_devkit_knowledge_base_join": tool_knowledge_base_join,
        "agent_devkit_knowledge_base_status": tool_knowledge_base_status,
        "agent_devkit_knowledge_base_tokens": tool_knowledge_base_tokens,
        "agent_devkit_knowledge_base_rotate_token": tool_knowledge_base_rotate_token,
        "agent_devkit_roadmap": tool_roadmap,
        "agent_devkit_source_list": tool_source_list,
        "agent_devkit_source_status": tool_source_status,
        "agent_devkit_wizard_show": tool_wizard_show,
        "agent_devkit_wizard_answer": tool_wizard_answer,
    }
    handler = handlers.get(name)
    if not handler:
        raise McpToolError(f"Unknown MCP tool: {name}")
    try:
        payload = handler(args)
    except (DevKitError, SourceRegistryError, WizardStateError, ValueError) as exc:
        payload = {
            "kind": "mcp-tool-error",
            "status": "failed",
            "ok": False,
            "tool": name,
            "message": str(exc),
            "origin": "mcp",
        }
    safe_payload = redact_value(payload)
    return tool_result(safe_payload, is_error=is_error_payload(safe_payload))


def list_mcp_tool_definitions() -> dict[str, Any]:
    return {
        "kind": "mcp-tools",
        "status": "ok",
        "tools": mcp_tools(),
    }


def tool_agents_list(_args: dict[str, Any]) -> dict[str, Any]:
    return list_agent_modules()


def tool_capabilities_list(args: dict[str, Any]) -> dict[str, Any]:
    return list_capability_modules(optional_string(args, "agent_id"))


def tool_capability_inspect(args: dict[str, Any]) -> dict[str, Any]:
    return inspect_capability_request(required_string(args, "agent_id"), required_string(args, "capability_id"))


def tool_capability_run(args: dict[str, Any]) -> dict[str, Any]:
    agent_id = required_string(args, "agent_id")
    capability_id = required_string(args, "capability_id")
    dry_run = optional_bool(args, "dry_run", default=False)
    inspected = inspect_capability_request(agent_id, capability_id)
    capability = inspected.get("capability") if isinstance(inspected.get("capability"), dict) else {}
    policy = str(capability.get("write_policy") or "")
    if policy != "read_only" and not dry_run:
        payload = {
            "kind": "run",
            "status": "blocked",
            "ok": False,
            "origin": "mcp",
            "agent": inspected.get("agent"),
            "capability": capability.get("id") or capability_id,
            "write_policy": policy,
            "write_policy_metadata": capability.get("write_policy_metadata"),
            "reason": "mcp_write_policy_blocked",
            "risks": ["MCP stdio v1 only executes read-only capabilities by default."],
            "next_steps": ["Call again with dry_run=true or use the CLI with explicit confirmation for write operations."],
            "exit_code": 2,
        }
        attach_mcp_audit(payload, tool="agent_devkit_capability_run", args=args)
        return payload

    request = CapabilityRunRequest(
        agent_id=agent_id,
        capability_id=capability_id,
        capability_args=string_list(args.get("args")),
        origin="mcp",
        request_id=optional_string(args, "request_id"),
        inputs=mapping_value(args.get("inputs")),
        source_id=optional_string(args, "source_id"),
        dry_run=dry_run,
    )
    payload = run_capability_request(request)
    attach_mcp_audit(payload, tool="agent_devkit_capability_run", args=args)
    return payload


def tool_doctor(args: dict[str, Any]) -> dict[str, Any]:
    return doctor(
        project=optional_string(args, "project"),
        home=optional_string(args, "home"),
        scope=optional_string(args, "scope") or "auto",
    )


def tool_onboarding_status(_args: dict[str, Any]) -> dict[str, Any]:
    return onboarding_status(ROOT)


def tool_memory_show(args: dict[str, Any]) -> dict[str, Any]:
    return show_memory(ROOT, agent_id=optional_string(args, "agent_id"), source_id=optional_string(args, "source_id"))


def tool_memory_path(_args: dict[str, Any]) -> dict[str, Any]:
    return memory_path_payload()


def tool_memory_reset(args: dict[str, Any]) -> dict[str, Any]:
    payload = reset_memory(
        all_memory=optional_bool(args, "all", default=False),
        agent_id=optional_string(args, "agent_id"),
        source_id=optional_string(args, "source_id"),
        reset_sessions=optional_bool(args, "sessions", default=False),
        reset_tasks=optional_bool(args, "tasks", default=False),
        reset_cache=optional_bool(args, "cache", default=False),
    )
    attach_mcp_audit(payload, tool="agent_devkit_memory_reset", args=args)
    return payload


def tool_memory_backup_create(args: dict[str, Any]) -> dict[str, Any]:
    payload = create_memory_backup(
        title=optional_string(args, "title"),
        encrypted=optional_bool(args, "encrypted", default=False),
        passphrase_env=optional_string(args, "passphrase_env"),
    )
    attach_mcp_audit(payload, tool="agent_devkit_memory_backup_create", args=args)
    return payload


def tool_memory_backup_list(_args: dict[str, Any]) -> dict[str, Any]:
    return list_memory_backups()


def tool_memory_backup_restore(args: dict[str, Any]) -> dict[str, Any]:
    backup_id = optional_string(args, "backup_id")
    backup_file = optional_string(args, "file")
    if not backup_id and not backup_file:
        raise ValueError("agent_devkit_memory_backup_restore requires backup_id or file")
    payload = restore_memory_backup(
        backup_id,
        yes=optional_bool(args, "yes", default=False),
        backup_file=backup_file,
        passphrase_env=optional_string(args, "passphrase_env"),
    )
    attach_mcp_audit(payload, tool="agent_devkit_memory_backup_restore", args=args)
    return payload


def tool_memory_backup_delete(args: dict[str, Any]) -> dict[str, Any]:
    payload = delete_memory_backup(required_string(args, "backup_id"), yes=optional_bool(args, "yes", default=False))
    attach_mcp_audit(payload, tool="agent_devkit_memory_backup_delete", args=args)
    return payload


def tool_shared_memory_list(_args: dict[str, Any]) -> dict[str, Any]:
    return shared_memory_list()


def tool_shared_memory_status(args: dict[str, Any]) -> dict[str, Any]:
    return shared_memory_status(required_string(args, "memory_id"))


def tool_shared_memory_create(args: dict[str, Any]) -> dict[str, Any]:
    payload = shared_memory_create(optional_string(args, "title"))
    attach_mcp_audit(payload, tool="agent_devkit_shared_memory_create", args=args)
    return payload


def tool_shared_memory_read(args: dict[str, Any]) -> dict[str, Any]:
    return shared_memory_read(
        required_string(args, "memory_id"),
        optional_string(args, "entry_id"),
        contributor_key=optional_string(args, "key"),
    )


def tool_shared_memory_submit(args: dict[str, Any]) -> dict[str, Any]:
    payload = shared_memory_submit(
        required_string(args, "memory_id"),
        title=optional_string(args, "title"),
        content=required_string(args, "content"),
        contributor_key=required_string(args, "key"),
    )
    attach_mcp_audit(payload, tool="agent_devkit_shared_memory_submit", args=args)
    return payload


def tool_shared_memory_review(args: dict[str, Any]) -> dict[str, Any]:
    return shared_memory_review(required_string(args, "memory_id"), required_string(args, "submission_id"))


def tool_shared_memory_publish(args: dict[str, Any]) -> dict[str, Any]:
    payload = shared_memory_publish(
        required_string(args, "memory_id"),
        required_string(args, "submission_id"),
        yes=optional_bool(args, "yes", default=False),
        owner_key=optional_string(args, "owner_key"),
    )
    attach_mcp_audit(payload, tool="agent_devkit_shared_memory_publish", args=args)
    return payload


def tool_personality_show(_args: dict[str, Any]) -> dict[str, Any]:
    return load_personality()


def tool_personality_update(args: dict[str, Any]) -> dict[str, Any]:
    payload = update_personality(
        agent_name=optional_string(args, "agent_name"),
        user_name=optional_string(args, "user_name"),
        language=optional_string(args, "language"),
        tone=optional_string(args, "tone"),
        detail_level=optional_string(args, "detail_level"),
    )
    attach_mcp_audit(payload, tool="agent_devkit_personality_update", args=args)
    return payload


def tool_personality_reset(args: dict[str, Any]) -> dict[str, Any]:
    payload = reset_personality()
    attach_mcp_audit(payload, tool="agent_devkit_personality_reset", args=args)
    return payload


def tool_task_list(_args: dict[str, Any]) -> dict[str, Any]:
    return list_tasks()


def tool_task_show(args: dict[str, Any]) -> dict[str, Any]:
    return show_task(required_string(args, "task_id"))


def tool_task_run_dry_run(args: dict[str, Any]) -> dict[str, Any]:
    return run_task(required_string(args, "task_id"), dry_run=True, origin="mcp")


def tool_scheduler_run_once_dry_run(_args: dict[str, Any]) -> dict[str, Any]:
    return scheduler_run_once(dry_run=True)


def tool_notifications_doctor(_args: dict[str, Any]) -> dict[str, Any]:
    return notification_doctor()


def tool_notifications_list_events(_args: dict[str, Any]) -> dict[str, Any]:
    return list_notification_events()


def tool_notifications_list_channels(_args: dict[str, Any]) -> dict[str, Any]:
    return list_notification_channels()


def tool_notifications_format(args: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "title": optional_string(args, "title") or "Agent DevKit",
        "message": optional_string(args, "message") or "",
        "summary": optional_string(args, "summary"),
        "event": optional_string(args, "event") or "task.completed",
        "status": optional_string(args, "status"),
        "severity": optional_string(args, "severity") or "info",
        "task_id": optional_string(args, "task_id"),
        "origin": optional_string(args, "origin") or "mcp",
    }
    return format_notification_event(payload)


def tool_catalog_list(args: dict[str, Any]) -> dict[str, Any]:
    item_type = optional_catalog_type(args)
    return catalog_list(ROOT, item_type=item_type, filters=catalog_filters(args))


def tool_catalog_search(args: dict[str, Any]) -> dict[str, Any]:
    item_type = optional_catalog_type(args)
    return catalog_search(required_string(args, "query"), ROOT, item_type=item_type)


def tool_catalog_show(args: dict[str, Any]) -> dict[str, Any]:
    item_type = optional_catalog_type(args)
    return catalog_show(required_string(args, "id"), ROOT, item_type=item_type)


def tool_route_explain(args: dict[str, Any]) -> dict[str, Any]:
    return explain_route(required_string(args, "prompt"), ROOT)


def tool_agent_prompt_dry_run(args: dict[str, Any]) -> dict[str, Any]:
    return build_execution_plan(ROOT, required_string(args, "prompt"), dry_run=True)


def tool_agentic_plan(args: dict[str, Any]) -> dict[str, Any]:
    return agentic_plan(ROOT, [required_string(args, "prompt")])


def tool_eval_list(_args: dict[str, Any]) -> dict[str, Any]:
    return eval_list()


def tool_eval_run(args: dict[str, Any]) -> dict[str, Any]:
    return eval_run(required_string(args, "suite"), ROOT)


def tool_secrets_doctor(_args: dict[str, Any]) -> dict[str, Any]:
    return secrets_doctor()


def tool_workflow_list(_args: dict[str, Any]) -> dict[str, Any]:
    return workflow_list(ROOT)


def tool_workflow_show(args: dict[str, Any]) -> dict[str, Any]:
    return workflow_show(required_string(args, "workflow_id"), ROOT)


def tool_workflow_run_dry_run(args: dict[str, Any]) -> dict[str, Any]:
    return workflow_run(required_string(args, "workflow_id"), dry_run=True, root=ROOT)


def tool_local_llm_list(_args: dict[str, Any]) -> dict[str, Any]:
    return local_llm_list()


def tool_local_llm_doctor(_args: dict[str, Any]) -> dict[str, Any]:
    return local_llm_doctor()


def tool_local_llm_models(_args: dict[str, Any]) -> dict[str, Any]:
    return local_llm_models()


def tool_local_artifacts_list(_args: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "local-artifacts",
        "status": "ok",
        "skills": skill_list(),
        "scripts": script_list(),
        "agents": local_agent_list(),
        "automations": local_automation_list(),
    }


def tool_local_skill_create(args: dict[str, Any]) -> dict[str, Any]:
    return skill_create(
        optional_string(args, "id"),
        description=optional_string(args, "description"),
        force=optional_bool(args, "force", default=False),
    )


def tool_local_skill_list(_args: dict[str, Any]) -> dict[str, Any]:
    return skill_list()


def tool_local_skill_show(args: dict[str, Any]) -> dict[str, Any]:
    return skill_show(required_string(args, "id"))


def tool_local_script_create(args: dict[str, Any]) -> dict[str, Any]:
    return script_create(
        optional_string(args, "id"),
        command=optional_string(args, "command"),
        force=optional_bool(args, "force", default=False),
    )


def tool_local_script_list(_args: dict[str, Any]) -> dict[str, Any]:
    return script_list()


def tool_local_script_run_dry_run(args: dict[str, Any]) -> dict[str, Any]:
    return script_run(required_string(args, "id"), dry_run=True)


def tool_local_agent_create(args: dict[str, Any]) -> dict[str, Any]:
    return local_agent_create(
        optional_string(args, "id"),
        description=optional_string(args, "description"),
        force=optional_bool(args, "force", default=False),
    )


def tool_local_agent_list(_args: dict[str, Any]) -> dict[str, Any]:
    return local_agent_list()


def tool_local_agent_show(args: dict[str, Any]) -> dict[str, Any]:
    return local_agent_show(required_string(args, "id"))


def tool_local_agent_validate(args: dict[str, Any]) -> dict[str, Any]:
    return local_agent_validate(required_string(args, "id"))


def tool_local_automation_create(args: dict[str, Any]) -> dict[str, Any]:
    return local_automation_create(
        optional_string(args, "id"),
        title=optional_string(args, "title"),
        prompt=optional_string(args, "prompt"),
        command=optional_string(args, "command"),
        every=optional_string(args, "every"),
        cron=optional_string(args, "cron"),
        force=optional_bool(args, "force", default=False),
    )


def tool_local_automation_list(_args: dict[str, Any]) -> dict[str, Any]:
    return local_automation_list()


def tool_local_automation_show(args: dict[str, Any]) -> dict[str, Any]:
    return local_automation_show(required_string(args, "id"))


def tool_local_automation_enable(args: dict[str, Any]) -> dict[str, Any]:
    return local_automation_enable(required_string(args, "id"), True)


def tool_local_automation_disable(args: dict[str, Any]) -> dict[str, Any]:
    return local_automation_enable(required_string(args, "id"), False)


def tool_local_automation_validate(args: dict[str, Any]) -> dict[str, Any]:
    return local_automation_validate(required_string(args, "id"))


def tool_team_status(args: dict[str, Any]) -> dict[str, Any]:
    return team_status(mcp_project(args))


def tool_team_doctor(args: dict[str, Any]) -> dict[str, Any]:
    return team_doctor(mcp_project(args))


def tool_team_init(args: dict[str, Any]) -> dict[str, Any]:
    return team_init(mcp_project(args), force=optional_bool(args, "force", default=False))


def tool_team_onboard(args: dict[str, Any]) -> dict[str, Any]:
    return team_onboard(mcp_project(args))


def tool_team_profile_list(args: dict[str, Any]) -> dict[str, Any]:
    return team_profile_list(mcp_project(args))


def tool_team_profile_show(args: dict[str, Any]) -> dict[str, Any]:
    return team_profile_show(optional_string(args, "profile_id"), mcp_project(args))


def tool_team_profile_export(args: dict[str, Any]) -> dict[str, Any]:
    return team_profile_export(optional_string(args, "profile_id"), optional_string(args, "path"), mcp_project(args))


def tool_team_profile_import(args: dict[str, Any]) -> dict[str, Any]:
    return team_profile_import(required_string(args, "path"), mcp_project(args))


def tool_knowledge_doctor(args: dict[str, Any]) -> dict[str, Any]:
    return knowledge_doctor(mcp_project(args))


def tool_knowledge_init(args: dict[str, Any]) -> dict[str, Any]:
    return knowledge_init(mcp_project(args), force=optional_bool(args, "force", default=False))


def tool_knowledge_index(args: dict[str, Any]) -> dict[str, Any]:
    return knowledge_index(mcp_project(args))


def tool_knowledge_search(args: dict[str, Any]) -> dict[str, Any]:
    return knowledge_search(required_string(args, "query"), mcp_project(args))


def tool_knowledge_curate(args: dict[str, Any]) -> dict[str, Any]:
    return knowledge_curate(mcp_project(args))


def tool_knowledge_sync(args: dict[str, Any]) -> dict[str, Any]:
    return knowledge_sync(mcp_project(args))


def tool_knowledge_snapshot_create(args: dict[str, Any]) -> dict[str, Any]:
    payload = knowledge_snapshot_create(
        title=required_string(args, "title"),
        content=optional_string(args, "content"),
        from_file=optional_string(args, "from_file"),
        entry_type=optional_string(args, "type"),
        project=mcp_project(args),
    )
    attach_mcp_audit(payload, tool="agent_devkit_knowledge_snapshot_create", args=args)
    return payload


def tool_knowledge_snapshot_list(args: dict[str, Any]) -> dict[str, Any]:
    return knowledge_snapshot_list(mcp_project(args))


def tool_knowledge_snapshot_show(args: dict[str, Any]) -> dict[str, Any]:
    return knowledge_snapshot_show(required_string(args, "snapshot_id"), mcp_project(args))


def tool_knowledge_snapshot_score(args: dict[str, Any]) -> dict[str, Any]:
    return knowledge_snapshot_score(required_string(args, "snapshot_id"), mcp_project(args))


def tool_knowledge_snapshot_submit(args: dict[str, Any]) -> dict[str, Any]:
    payload = knowledge_snapshot_submit(required_string(args, "snapshot_id"), mcp_project(args))
    attach_mcp_audit(payload, tool="agent_devkit_knowledge_snapshot_submit", args=args)
    return payload


def tool_knowledge_review_list(args: dict[str, Any]) -> dict[str, Any]:
    return knowledge_review_list(mcp_project(args))


def tool_knowledge_review(args: dict[str, Any]) -> dict[str, Any]:
    payload = knowledge_review(required_string(args, "snapshot_id"), mcp_project(args))
    attach_mcp_audit(payload, tool="agent_devkit_knowledge_review", args=args)
    return payload


def tool_knowledge_publish(args: dict[str, Any]) -> dict[str, Any]:
    payload = knowledge_publish(
        required_string(args, "snapshot_id"),
        mcp_project(args),
        yes=optional_bool(args, "yes", default=False),
        owner_agent=optional_string(args, "owner_agent"),
    )
    attach_mcp_audit(payload, tool="agent_devkit_knowledge_publish", args=args)
    return payload


def tool_knowledge_base_create(args: dict[str, Any]) -> dict[str, Any]:
    payload = knowledge_base_create(
        mcp_project(args),
        provider=optional_string(args, "provider"),
        force=optional_bool(args, "force", default=False),
    )
    attach_mcp_audit(payload, tool="agent_devkit_knowledge_base_create", args=args)
    return payload


def tool_knowledge_base_join(args: dict[str, Any]) -> dict[str, Any]:
    payload = knowledge_base_join(
        required_string(args, "kb_id"),
        mcp_project(args),
        provider=optional_string(args, "provider"),
        force=optional_bool(args, "force", default=False),
    )
    attach_mcp_audit(payload, tool="agent_devkit_knowledge_base_join", args=args)
    return payload


def tool_knowledge_base_status(args: dict[str, Any]) -> dict[str, Any]:
    return knowledge_base_status(mcp_project(args))


def tool_knowledge_base_tokens(args: dict[str, Any]) -> dict[str, Any]:
    return knowledge_base_tokens(mcp_project(args))


def tool_knowledge_base_rotate_token(args: dict[str, Any]) -> dict[str, Any]:
    payload = knowledge_base_rotate_token(required_string(args, "scope"), mcp_project(args))
    attach_mcp_audit(payload, tool="agent_devkit_knowledge_base_rotate_token", args=args)
    return payload


def tool_roadmap(_args: dict[str, Any]) -> dict[str, Any]:
    return roadmap_payload(ROOT)


def tool_source_list(_args: dict[str, Any]) -> dict[str, Any]:
    return list_sources()


def tool_source_status(args: dict[str, Any]) -> dict[str, Any]:
    return source_status(optional_string(args, "source_id"))


def tool_wizard_show(args: dict[str, Any]) -> dict[str, Any]:
    return show_wizard(required_string(args, "wizard_id"))


def tool_wizard_answer(args: dict[str, Any]) -> dict[str, Any]:
    payload = answer_wizard(required_string(args, "wizard_id"), required_string(args, "answer"))
    attach_mcp_audit(payload, tool="agent_devkit_wizard_answer", args=args)
    return payload


def attach_mcp_audit(payload: dict[str, Any], *, tool: str, args: dict[str, Any]) -> None:
    audit_result = try_record_audit(
        command=tool,
        args={"command": "mcp", "tool": tool, "arguments": redact_value(args, redact_access_keys=True)},
        result=payload,
        error=None,
        origin="mcp",
        required=False,
    )
    if audit_result.get("audit_warning"):
        payload["audit_warning"] = audit_result["audit_warning"]
    elif audit_result.get("audit"):
        payload["audit"] = audit_result["audit"]


def tool_result(payload: dict[str, Any], *, is_error: bool) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            }
        ],
        "structuredContent": payload,
        "isError": bool(is_error),
    }


def is_error_payload(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    status = str(payload.get("status") or "")
    return payload.get("ok") is False or status in {"blocked", "failed", "error"}


def required_string(args: dict[str, Any], key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value.strip():
        raise McpToolError(f"{key} is required")
    return value.strip()


def optional_string(args: dict[str, Any], key: str) -> str | None:
    value = args.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise McpToolError(f"{key} must be a string")
    return value.strip() or None


def mcp_project(args: dict[str, Any]) -> Path | None:
    project = optional_string(args, "project")
    return Path(project).expanduser().resolve() if project else None


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise McpToolError("args must be an array of strings")
    return list(value)


def mapping_value(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise McpToolError("inputs must be an object")
    return dict(value)


def optional_bool(args: dict[str, Any], key: str, *, default: bool) -> bool:
    value = args.get(key, default)
    if not isinstance(value, bool):
        raise McpToolError(f"{key} must be a boolean")
    return value


def optional_catalog_type(args: dict[str, Any]) -> str | None:
    item_type = optional_string(args, "type")
    allowed = {
        None,
        "agent",
        "capability",
        "provider",
        "workflow",
        "tool",
        "skill",
        "plugin",
        "extension",
        "script",
        "local-agent",
        "automation",
    }
    if item_type not in allowed:
        raise McpToolError("type must be a known Agent DevKit catalog type")
    return item_type


def catalog_filters(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": optional_string(args, "provider"),
        "status": optional_string(args, "status"),
        "write_policy": optional_string(args, "write_policy"),
        "readiness": optional_string(args, "readiness"),
    }
