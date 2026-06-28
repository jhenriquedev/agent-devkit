"""Setup wizard orchestration for Agent DevKit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.aikit.toolchain import setup_plan


def setup_wizard(root: Path, *, dry_run: bool = False, yes: bool = False) -> dict[str, Any]:
    return setup_plan(root, dry_run=dry_run, yes=yes)
