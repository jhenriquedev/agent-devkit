"""Core runtime facade independent from CLI argument parsing."""

from __future__ import annotations

from typing import Any

from cli.aikit.capability_runtime import (
    list_agents,
    list_all_capabilities,
    list_capabilities,
    load_agent,
    load_capability,
    run_capability,
    summarize_agent,
)
from cli.aikit.core.capability_contract import structured_inputs_to_argv
from cli.aikit.core.requests import AgentPromptRequest, CapabilityRunRequest
from cli.aikit.natural_prompt_runtime import run_agent_prompt_request


def run_agent_prompt(request: AgentPromptRequest) -> dict[str, Any]:
    return run_agent_prompt_request(request)


def list_agent_modules() -> dict[str, Any]:
    return {"kind": "agents", "items": list_agents()}


def list_capability_modules(agent_id: str | None = None) -> dict[str, Any]:
    if agent_id:
        agent = load_agent(agent_id)
        return {
            "kind": "capabilities",
            "agent": agent["id"],
            "items": list_capabilities(agent["path"]),
        }
    return {
        "kind": "capabilities",
        "agent": None,
        "items": list_all_capabilities(),
    }


def inspect_capability_request(agent_id: str, capability_id: str) -> dict[str, Any]:
    agent = load_agent(agent_id)
    capability = load_capability(agent["path"], capability_id)
    return {
        "kind": "capability",
        "agent": summarize_agent(agent),
        "capability": capability,
    }


def run_capability_request(request: CapabilityRunRequest) -> dict[str, Any]:
    agent = load_agent(request.agent_id)
    return run_capability(
        agent,
        request.capability_id,
        structured_inputs_to_argv(request),
        capture_output=request.capture_output,
        origin=request.origin,
        request_id=request.request_id,
        request_data=dict(request.inputs or {}),
    )
