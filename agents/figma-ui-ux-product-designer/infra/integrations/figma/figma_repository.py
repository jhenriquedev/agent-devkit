"""Figma integration contract for figma-ui-ux-product-designer.

This repository intentionally does not embed Figma credentials or call the Figma
API directly. In Codex/Figma-enabled runtimes, direct writes are performed by
MCP tools exposed to the agent. The local CLI uses this module to classify the
available mode and to generate safe action plans when direct mode is not
available.
"""

from __future__ import annotations

from pathlib import Path
import os


def read_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def detect_mode(project_root: Path | None = None) -> dict[str, str]:
    root = project_root or Path.cwd()
    env = read_env(root / ".env") | dict(os.environ)
    direct_flag = env.get("FIGMA_MCP_ENABLED", "").lower() in {"1", "true", "yes", "sim"}
    direct_flag = direct_flag or env.get("FIGMA_DIRECT_MODE", "").lower() in {"1", "true", "yes", "sim"}
    has_secret_or_plan = bool(env.get("FIGMA_ACCESS_TOKEN") or env.get("FIGMA_DEFAULT_PLAN_KEY"))
    if direct_flag and has_secret_or_plan:
        return {"mode": "direct", "credentials": "present"}
    return {"mode": "plan_only", "credentials": "missing_or_not_declared"}
