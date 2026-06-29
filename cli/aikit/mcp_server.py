"""Minimal MCP stdio server for Agent DevKit."""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from cli.aikit.mcp_manifest import MCP_PROTOCOL_VERSION, MCP_SERVER_NAME, mcp_doctor, mcp_manifest, mcp_tools
from cli.aikit.mcp_tools import McpToolError, call_mcp_tool


JSONRPC_VERSION = "2.0"
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class McpMethodNotFound(ValueError):
    """Raised when a JSON-RPC method is not supported by this MCP server."""


def serve_mcp_stdio(stdin: TextIO | None = None, stdout: TextIO | None = None, stderr: TextIO | None = None) -> None:
    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    error_stream = stderr or sys.stderr
    for raw_line in input_stream:
        line = raw_line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            write_message(output_stream, error_response(None, PARSE_ERROR, "Parse error", data={"message": str(exc)}))
            continue
        if not isinstance(message, dict):
            write_message(output_stream, error_response(None, INVALID_REQUEST, "Invalid Request"))
            continue
        response = handle_message(message, stderr=error_stream)
        if response is not None:
            write_message(output_stream, response)


def handle_message(message: dict[str, Any], *, stderr: TextIO | None = None) -> dict[str, Any] | None:
    request_id = message.get("id")
    method = message.get("method")
    if message.get("jsonrpc") != JSONRPC_VERSION or not isinstance(method, str):
        return error_response(request_id, INVALID_REQUEST, "Invalid Request")
    if request_id is None:
        handle_notification(method)
        return None
    try:
        result = dispatch_request(method, message.get("params"))
    except McpMethodNotFound as exc:
        return error_response(request_id, METHOD_NOT_FOUND, str(exc))
    except McpToolError as exc:
        return error_response(request_id, INVALID_PARAMS, str(exc))
    except Exception as exc:  # noqa: BLE001 - protocol response must hide stack traces.
        if stderr:
            print(f"agent-devkit MCP internal error: {type(exc).__name__}", file=stderr)
        return error_response(request_id, INTERNAL_ERROR, "Internal error")
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "result": result,
    }


def dispatch_request(method: str, params: Any) -> dict[str, Any]:
    if method == "initialize":
        return initialize_result(params)
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": mcp_tools()}
    if method == "tools/call":
        if not isinstance(params, dict):
            raise McpToolError("tools/call params must be an object")
        name = params.get("name")
        if not isinstance(name, str) or not name.strip():
            raise McpToolError("tools/call requires a tool name")
        arguments = params.get("arguments", {})
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise McpToolError("tools/call arguments must be an object")
        return call_mcp_tool(name.strip(), arguments)
    raise McpMethodNotFound(f"Method not found: {method}")


def initialize_result(params: Any) -> dict[str, Any]:
    requested_version = None
    if isinstance(params, dict):
        requested_version = params.get("protocolVersion")
    return {
        "protocolVersion": str(requested_version or MCP_PROTOCOL_VERSION),
        "capabilities": {
            "tools": {},
        },
        "serverInfo": {
            "name": MCP_SERVER_NAME,
            "version": str(mcp_manifest()["server"]["version"]),
        },
    }


def handle_notification(method: str) -> None:
    if method in {"notifications/initialized", "notifications/cancelled"}:
        return
    return


def mcp_cli_doctor() -> dict[str, Any]:
    return mcp_doctor()


def write_message(stdout: TextIO, message: dict[str, Any]) -> None:
    stdout.write(json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n")
    stdout.flush()


def error_response(request_id: Any, code: int, message: str, *, data: Any | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": error,
    }
