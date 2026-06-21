#!/usr/bin/env python3
"""Runner for data-scientist-analyst/calculate-sample-size."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))

from runner_support import run_dataset_capability  # pylint: disable=import-error


if __name__ == "__main__":
    raise SystemExit(run_dataset_capability("calculate-sample-size"))
