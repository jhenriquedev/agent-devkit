"""Layout engine placeholder for future Draw.io layout strategies.

The MVP layout lives in drawio_renderer.py to keep the first implementation
small. This module exists as the integration boundary for future layered,
swimlane, C4 and ERD-specific layout algorithms.
"""

from __future__ import annotations

from typing import Any


def recommend_layout(diagram_type: str | None, node_count: int) -> dict[str, Any]:
    direction = "left-to-right"
    if diagram_type in {"erd", "data_lineage"}:
        direction = "top-to-bottom"
    return {"direction": direction, "split_recommended": node_count > 12}
