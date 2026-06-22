"""Executable bridge for real Figma MCP operations.

The local ai-devkit CLI cannot call Codex tool objects directly. For production
usage, a host runtime exposes a small bridge command through
FIGMA_MCP_BRIDGE_COMMAND. This adapter sends one JSON request to stdin and
expects one JSON response on stdout.
"""

from __future__ import annotations

import json
from pathlib import Path
import os
import shlex
import subprocess
from typing import Any

try:
    from .figma_models import FigmaOperation
except ImportError:  # pragma: no cover - used when loaded by path
    from figma_models import FigmaOperation


class FigmaMcpBridgeError(RuntimeError):
    """Raised when the configured bridge cannot execute the Figma operation."""


class FigmaMcpAdapter:
    def __init__(self, command: str, project_root: Path, timeout_seconds: int = 120) -> None:
        if not command.strip():
            raise FigmaMcpBridgeError("FIGMA_MCP_BRIDGE_COMMAND nao configurado.")
        self.command = command
        self.project_root = project_root
        self.timeout_seconds = timeout_seconds

    def execute(self, operation: FigmaOperation) -> dict[str, Any]:
        request = {
            "kind": "figma_mcp_operation",
            "version": "1.0",
            "operation": operation.as_dict(),
            "env": safe_request_env(os.environ),
        }
        try:
            process = subprocess.run(
                shlex.split(self.command),
                input=json.dumps(request, ensure_ascii=False),
                cwd=self.project_root,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise FigmaMcpBridgeError(f"bridge Figma nao encontrado: {exc}") from exc
        except subprocess.TimeoutExpired as exc:
            raise FigmaMcpBridgeError(f"bridge Figma excedeu timeout de {self.timeout_seconds}s") from exc

        if process.returncode != 0:
            detail = process.stderr.strip() or process.stdout.strip() or f"exit code {process.returncode}"
            raise FigmaMcpBridgeError(f"bridge Figma falhou: {detail}")
        try:
            payload = json.loads(process.stdout)
        except json.JSONDecodeError as exc:
            raise FigmaMcpBridgeError("bridge Figma retornou stdout que nao e JSON valido") from exc
        validate_execution_payload(payload)
        return payload


def safe_request_env(env: dict[str, str]) -> dict[str, str]:
    allowed_prefixes = ("FIGMA_DEFAULT_", "TEST_")
    allowed_names = {
        "FIGMA_MCP_ENABLED",
        "FIGMA_DIRECT_MODE",
    }
    return {
        key: value
        for key, value in env.items()
        if key in allowed_names or key.startswith(allowed_prefixes)
    }


def validate_execution_payload(payload: dict[str, Any]) -> None:
    if payload.get("status") not in {"executed", "updated", "created", "inspected"}:
        raise FigmaMcpBridgeError("bridge Figma nao confirmou status executado/atualizado/criado/inspecionado")
    evidence = [
        payload.get("file_key"),
        payload.get("file_url"),
        payload.get("created_node_ids"),
        payload.get("mutated_node_ids"),
        payload.get("inspected_node_ids"),
    ]
    if not any(evidence):
        raise FigmaMcpBridgeError("bridge Figma nao retornou file_key, file_url ou node IDs")

