#!/usr/bin/env python3
"""Runner for search-columns."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))

from strong_runner import run_capability  # pylint: disable=import-error


if __name__ == "__main__":
    raise SystemExit(run_capability("search-columns"))
