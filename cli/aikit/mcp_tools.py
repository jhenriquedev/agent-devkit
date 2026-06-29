"""MCP tool adapters over the Agent DevKit core runtime."""

from __future__ import annotations

import json
from typing import Any, Callable

from cli.aikit.audit import redact_value, try_record_audit
from cli.aikit.catalog import catalog_search
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
from cli.aikit.mcp_manifest import mcp_tools
from cli.aikit.orchestrator import build_execution_plan
from cli.aikit.roadmap_cli import roadmap_payload
from cli.aikit.router_explain import explain_route
from cli.aikit.runtime_paths import ROOT
from cli.aikit.secrets import secrets_doctor
from cli.aikit.sources import SourceRegistryError, list_sources, source_status
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
        "agent_devkit_catalog_search": tool_catalog_search,
        "agent_devkit_route_explain": tool_route_explain,
        "agent_devkit_agent_prompt_dry_run": tool_agent_prompt_dry_run,
        "agent_devkit_eval_list": tool_eval_list,
        "agent_devkit_eval_run": tool_eval_run,
        "agent_devkit_secrets_doctor": tool_secrets_doctor,
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


def tool_catalog_search(args: dict[str, Any]) -> dict[str, Any]:
    item_type = optional_string(args, "type")
    if item_type not in {None, "agent", "capability", "provider"}:
        raise McpToolError("type must be agent, capability or provider")
    return catalog_search(required_string(args, "query"), ROOT, item_type=item_type)


def tool_route_explain(args: dict[str, Any]) -> dict[str, Any]:
    return explain_route(required_string(args, "prompt"), ROOT)


def tool_agent_prompt_dry_run(args: dict[str, Any]) -> dict[str, Any]:
    return build_execution_plan(ROOT, required_string(args, "prompt"), dry_run=True)


def tool_eval_list(_args: dict[str, Any]) -> dict[str, Any]:
    return eval_list()


def tool_eval_run(args: dict[str, Any]) -> dict[str, Any]:
    return eval_run(required_string(args, "suite"), ROOT)


def tool_secrets_doctor(_args: dict[str, Any]) -> dict[str, Any]:
    return secrets_doctor()


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
        args={"command": "mcp", "tool": tool, "arguments": redact_value(args)},
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
