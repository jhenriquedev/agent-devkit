"""MCP manifest and tool schemas for Agent DevKit."""

from __future__ import annotations

from typing import Any

from cli.aikit import __version__


MCP_PROTOCOL_VERSION = "2025-11-25"
MCP_SERVER_NAME = "agent-devkit"


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "agent_devkit_agents_list",
        "description": "List available Agent DevKit agents.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_capabilities_list",
        "description": "List available capabilities, optionally filtered by agent id.",
        "inputSchema": {
            "type": "object",
            "properties": {"agent_id": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_capability_inspect",
        "description": "Inspect one capability contract.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "capability_id": {"type": "string"},
            },
            "required": ["agent_id", "capability_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_capability_run",
        "description": "Run a read-only capability or dry-run a non-read-only capability through Agent DevKit core.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "capability_id": {"type": "string"},
                "args": {"type": "array", "items": {"type": "string"}},
                "inputs": {"type": "object"},
                "source_id": {"type": "string"},
                "dry_run": {"type": "boolean"},
                "request_id": {"type": "string"},
            },
            "required": ["agent_id", "capability_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_doctor",
        "description": "Return local Agent DevKit diagnostics.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "home": {"type": "string"},
                "scope": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_source_list",
        "description": "List configured sources without exposing secrets.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_source_status",
        "description": "Inspect source readiness without exposing secrets.",
        "inputSchema": {
            "type": "object",
            "properties": {"source_id": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_wizard_show",
        "description": "Show a pending setup wizard.",
        "inputSchema": {
            "type": "object",
            "properties": {"wizard_id": {"type": "string"}},
            "required": ["wizard_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_wizard_answer",
        "description": "Answer a pending setup wizard question.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "wizard_id": {"type": "string"},
                "answer": {"type": "string"},
            },
            "required": ["wizard_id", "answer"],
            "additionalProperties": False,
        },
    },
]


def mcp_manifest() -> dict[str, Any]:
    return {
        "kind": "mcp-manifest",
        "status": "ok",
        "schema_version": "ai-devkit.mcp-manifest/v1",
        "protocol_version": MCP_PROTOCOL_VERSION,
        "transport": "stdio",
        "server": {
            "name": MCP_SERVER_NAME,
            "version": __version__,
        },
        "tools": mcp_tools(),
        "host_config": {
            "mcpServers": {
                MCP_SERVER_NAME: {
                    "command": "agent",
                    "args": ["mcp", "serve"],
                }
            }
        },
    }


def mcp_tools_payload() -> dict[str, Any]:
    return {
        "kind": "mcp-tools",
        "status": "ok",
        "protocol_version": MCP_PROTOCOL_VERSION,
        "transport": "stdio",
        "tools": mcp_tools(),
    }


def mcp_tools() -> list[dict[str, Any]]:
    return [dict(tool) for tool in TOOL_DEFINITIONS]


def mcp_doctor() -> dict[str, Any]:
    return {
        "kind": "mcp-doctor",
        "status": "ok",
        "protocol_version": MCP_PROTOCOL_VERSION,
        "transport": "stdio",
        "server": {
            "name": MCP_SERVER_NAME,
            "version": __version__,
        },
        "tools": {
            "count": len(TOOL_DEFINITIONS),
            "names": [tool["name"] for tool in TOOL_DEFINITIONS],
        },
        "checks": {
            "stdio_transport": True,
            "json_rpc": True,
            "core_runtime": True,
            "secrets_redacted": True,
            "host_specific_dependency": False,
        },
    }
