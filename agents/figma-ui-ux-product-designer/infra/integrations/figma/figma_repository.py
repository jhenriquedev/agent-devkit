"""Figma integration contract for figma-ui-ux-product-designer.

This repository intentionally does not embed Figma credentials. In local CLI
execution, direct writes are performed by a configured MCP bridge command. In
Codex/Figma-enabled runtimes, the bridge can wrap tools such as create_new_file,
use_figma, get_metadata, get_screenshot, search_design_system and get_libraries.
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
