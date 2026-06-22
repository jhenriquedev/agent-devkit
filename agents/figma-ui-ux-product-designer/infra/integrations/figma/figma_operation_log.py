"""Markdown and JSON operation logs for Figma executions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_execution_artifacts(output_dir: Path, result: dict[str, Any]) -> None:
    (output_dir / "figma-execution-result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "design-operation-log.md").write_text(render_operation_log(result), encoding="utf-8")


def render_operation_log(result: dict[str, Any]) -> str:
    created = result.get("created_node_ids") or []
    mutated = result.get("mutated_node_ids") or []
    inspected = result.get("inspected_node_ids") or []
    screenshots = result.get("screenshot_refs") or []
    return f"""# Design Operation Log

## Status

- Status: `{result.get('status', '-')}`
- Figma file: {result.get('file_url') or result.get('file_key') or '-'}
- Page: {result.get('page_name') or '-'}

## Evidence

- Created node IDs: {', '.join(created) if created else '-'}
- Mutated node IDs: {', '.join(mutated) if mutated else '-'}
- Inspected node IDs: {', '.join(inspected) if inspected else '-'}
- Screenshots: {', '.join(screenshots) if screenshots else '-'}

## Notes

Esta entrega foi executada via Figma MCP bridge. O agente so marca execucao real
quando o bridge retorna arquivo Figma, node IDs ou evidencias de inspecao.
"""

