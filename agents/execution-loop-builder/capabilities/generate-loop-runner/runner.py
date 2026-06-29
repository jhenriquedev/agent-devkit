#!/usr/bin/env python3
"""Runner for execution-loop-builder/generate-loop-runner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "execution-loop"
sys.path.insert(0, str(REPOSITORY_DIR))

from execution_loop_repository import ExecutionLoopBuilderError, ExecutionLoopRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an execution loop runner")
    parser.add_argument("--spec", required=True)
    args = parser.parse_args()
    try:
        result = ExecutionLoopRepository().generate_loop_runner(spec_path=Path(args.spec))
    except ExecutionLoopBuilderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
