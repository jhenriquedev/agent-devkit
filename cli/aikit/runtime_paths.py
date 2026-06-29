"""Shared runtime paths for the Agent DevKit CLI."""

from __future__ import annotations

import os
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(os.environ.get("AI_DEVKIT_ROOT", DEFAULT_ROOT)).resolve()
AGENTS_DIR = ROOT / "agents"
