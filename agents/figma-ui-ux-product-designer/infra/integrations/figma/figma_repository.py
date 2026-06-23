"""Figma integration entry point for figma-ui-ux-product-designer.

This module exposes `detect_mode` as the public API for capability runners to
determine the current Figma operation mode (direct_mcp, local_mcp_bridge,
plan_only, blocked).

All Figma write operations are routed through FigmaMcpAdapter (figma_mcp_adapter.py),
which in turn calls the configured MCP bridge command. This repository does NOT
embed credentials; it only delegates to the bridge via subprocess.

Figma tools used by the bridge (via Codex/Figma MCP):
  - create_new_file, use_figma, get_metadata, get_screenshot,
    search_design_system, get_libraries, generate_diagram.
These are invoked by bin/figma-codex-bridge.py, not by this module directly.
"""

from __future__ import annotations

from pathlib import Path

try:
    from .figma_mode import detect_mode as detect_figma_mode
except ImportError:  # pragma: no cover - used when loaded by path
    from figma_mode import detect_mode as detect_figma_mode


def detect_mode(project_root: Path | None = None) -> dict[str, str]:
    root = project_root or Path.cwd()
    return detect_figma_mode(root).as_dict()
