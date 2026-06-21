#!/usr/bin/env python3
"""Runner for decide-n1-outcome."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))

from auxiliary_runner import run  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run("decide-n1-outcome"))
