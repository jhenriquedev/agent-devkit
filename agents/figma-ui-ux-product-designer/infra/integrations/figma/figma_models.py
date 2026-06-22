"""Typed contracts for Figma execution through an MCP bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FigmaMode:
    mode: str
    reason: str
    credentials: str
    bridge_command: str | None = None

    def as_dict(self) -> dict[str, str]:
        payload = {
            "mode": self.mode,
            "reason": self.reason,
            "credentials": self.credentials,
        }
        if self.bridge_command:
            payload["bridge_command"] = "configured"
        return payload


@dataclass(frozen=True)
class FigmaOperation:
    capability: str
    action: str
    file_name: str
    page_name: str
    platform: str
    scope: str
    screens: list[str]
    components: list[str]
    brief: str = ""
    feedback: str = ""
    figma_file_url: str | None = None
    figma_project_url: str | None = None
    figma_file_key: str | None = None
    figma_node_id: str | None = None
    plan_key: str | None = None
    url: str | None = None
    design_style: str | None = None
    target_audience: str | None = None
    source_summaries: list[dict[str, str]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "action": self.action,
            "file_name": self.file_name,
            "page_name": self.page_name,
            "platform": self.platform,
            "scope": self.scope,
            "screens": self.screens,
            "components": self.components,
            "brief": self.brief,
            "feedback": self.feedback,
            "figma_file_url": self.figma_file_url,
            "figma_project_url": self.figma_project_url,
            "figma_file_key": self.figma_file_key,
            "figma_node_id": self.figma_node_id,
            "plan_key": self.plan_key,
            "url": self.url,
            "design_style": self.design_style,
            "target_audience": self.target_audience,
            "source_summaries": self.source_summaries,
        }

