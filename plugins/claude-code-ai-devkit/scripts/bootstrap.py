#!/usr/bin/env python3
"""Bootstrap checks for the Claude Code AI DevKit plugin."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from runtime import agent_command


def main() -> int:
    command, runtime_root = agent_command(Path(__file__))
    payload = {
        "kind": "plugin-bootstrap",
        "plugin": "claude-code-ai-devkit",
        "runtime_root": str(runtime_root),
        "agent_command": command,
        "agent_path": command[-1] if command else None,
        "agent_exists": command is not None,
        "agent_on_path": shutil.which("agent") is not None,
        "next_steps": [
            "Run devkit-doctor.",
            "Configure providers only when a task needs them.",
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if command else 2


if __name__ == "__main__":
    raise SystemExit(main())
