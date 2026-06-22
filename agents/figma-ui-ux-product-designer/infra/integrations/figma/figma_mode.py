"""Figma execution mode detection."""

from __future__ import annotations

from pathlib import Path
import os

try:
    from .figma_models import FigmaMode
except ImportError:  # pragma: no cover - used when loaded by path
    from figma_models import FigmaMode


TRUE_VALUES = {"1", "true", "yes", "sim", "on"}


def read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def merged_env(project_root: Path) -> dict[str, str]:
    process_env = dict(os.environ)
    if process_env.get("AI_DEVKIT_IGNORE_ENV_FILE", "").lower() in TRUE_VALUES:
        return process_env
    return read_env_file(project_root / ".env") | process_env


def detect_mode(project_root: Path, require_direct: bool = False) -> FigmaMode:
    env = merged_env(project_root)
    bridge_command = env.get("FIGMA_MCP_BRIDGE_COMMAND", "").strip()
    direct_flag = env.get("FIGMA_MCP_ENABLED", "").lower() in TRUE_VALUES
    direct_flag = direct_flag or env.get("FIGMA_DIRECT_MODE", "").lower() in TRUE_VALUES
    has_plan = bool(env.get("FIGMA_DEFAULT_PLAN_KEY"))

    if bridge_command and direct_flag:
        credentials = "plan_key_present" if has_plan else "bridge_configured"
        return FigmaMode(
            mode="direct_mcp",
            reason="Figma MCP bridge configurado. Escritas exigem confirmacao e retorno real do bridge.",
            credentials=credentials,
            bridge_command=bridge_command,
        )
    if bridge_command:
        return FigmaMode(
            mode="local_mcp_bridge",
            reason="FIGMA_MCP_BRIDGE_COMMAND existe, mas FIGMA_MCP_ENABLED/FIGMA_DIRECT_MODE nao esta ativo.",
            credentials="bridge_configured",
            bridge_command=bridge_command,
        )
    if require_direct:
        return FigmaMode(
            mode="blocked",
            reason=(
                "Figma direct_mcp requerido, mas FIGMA_MCP_BRIDGE_COMMAND e "
                "FIGMA_MCP_ENABLED/FIGMA_DIRECT_MODE nao foram detectados."
            ),
            credentials="missing_or_not_declared",
        )
    return FigmaMode(
        mode="plan_only",
        reason="Figma MCP bridge nao detectado no processo CLI; gerando plano executavel.",
        credentials="missing_or_not_declared",
    )
