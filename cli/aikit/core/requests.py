"""Structured requests for reusable Agent DevKit core calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


CAPABILITY_RUN_ORIGINS = {"cli", "mcp", "scheduler", "agent-prompt", "core"}


@dataclass(frozen=True)
class AgentPromptRequest:
    prompt: str
    llm: str | None = None
    dry_run: bool = False
    session_id: str | None = None
    new_session: bool = False
    no_llm_fallback: bool = False
    prog_name: str = "agent"
    project: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.prompt, str):
            raise ValueError("AgentPromptRequest.prompt must be a string")
        if not isinstance(self.prog_name, str) or not self.prog_name.strip():
            raise ValueError("AgentPromptRequest.prog_name must be a non-empty string")


@dataclass(frozen=True)
class CapabilityRunRequest:
    agent_id: str
    capability_id: str
    capability_args: Iterable[str] = ()
    capture_output: bool = True
    origin: str = "core"
    request_id: str | None = None
    inputs: dict[str, Any] | None = None
    source_id: str | None = None
    dry_run: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.agent_id, str) or not self.agent_id.strip():
            raise ValueError("CapabilityRunRequest.agent_id must be a non-empty string")
        if not isinstance(self.capability_id, str) or not self.capability_id.strip():
            raise ValueError("CapabilityRunRequest.capability_id must be a non-empty string")
        if self.capability_args is None:
            object.__setattr__(self, "capability_args", ())
        elif isinstance(self.capability_args, str):
            raise ValueError("CapabilityRunRequest.capability_args must be an iterable of strings, not a string")
        args = tuple(self.capability_args)
        if not all(isinstance(item, str) for item in args):
            raise ValueError("CapabilityRunRequest.capability_args must contain only strings")
        object.__setattr__(self, "capability_args", args)
        if not isinstance(self.capture_output, bool):
            raise ValueError("CapabilityRunRequest.capture_output must be a boolean")
        if self.origin not in CAPABILITY_RUN_ORIGINS:
            allowed = ", ".join(sorted(CAPABILITY_RUN_ORIGINS))
            raise ValueError(f"CapabilityRunRequest.origin must be one of: {allowed}")
        if self.request_id is not None and not isinstance(self.request_id, str):
            raise ValueError("CapabilityRunRequest.request_id must be a string when provided")
        if self.source_id is not None and not isinstance(self.source_id, str):
            raise ValueError("CapabilityRunRequest.source_id must be a string when provided")
        if self.inputs is None:
            object.__setattr__(self, "inputs", {})
        elif not isinstance(self.inputs, dict):
            raise ValueError("CapabilityRunRequest.inputs must be a mapping when provided")
        if not isinstance(self.dry_run, bool):
            raise ValueError("CapabilityRunRequest.dry_run must be a boolean")
