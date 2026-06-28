"""Runtime resolution helpers for installed AI DevKit plugin scripts."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def run_agent(script_file: str, args: list[str]) -> int:
    command, cwd = agent_command(Path(script_file))
    if command is None:
        print("error: agent runtime not found. Install or expose the agent command first.", file=sys.stderr)
        return 2
    return subprocess.run([*command, *args], cwd=cwd, check=False).returncode


def agent_command(script_path: Path) -> tuple[list[str] | None, Path]:
    for parent in script_path.resolve().parents:
        repo_agent = parent / "agent"
        if repo_agent.exists() and (parent / "agents").is_dir():
            return [sys.executable, str(repo_agent)], parent

        repo_aikit = parent / "aikit"
        if repo_aikit.exists() and (parent / "agents").is_dir():
            return [sys.executable, str(repo_aikit)], parent

        config_root = runtime_root_from_config(parent / ".ai-devkit" / "config.yaml")
        if config_root:
            config_agent = config_root / "agent"
            if config_agent.exists():
                return [sys.executable, str(config_agent)], config_root
            config_aikit = config_root / "aikit"
            if config_aikit.exists():
                return [sys.executable, str(config_aikit)], config_root

    agent_on_path = shutil.which("agent")
    if agent_on_path:
        return [agent_on_path], Path.cwd()
    on_path = shutil.which("aikit")
    if on_path:
        return [on_path], Path.cwd()
    return None, Path.cwd()


def runtime_root_from_config(path: Path) -> Path | None:
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("root:"):
            continue
        raw_value = stripped.split(":", 1)[1].strip()
        if not raw_value:
            return None
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            value = raw_value.strip('"').strip("'")
        return Path(value).expanduser().resolve()
    return None
