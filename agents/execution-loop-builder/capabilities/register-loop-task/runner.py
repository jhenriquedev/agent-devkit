#!/usr/bin/env python3
"""Runner for execution-loop-builder/register-loop-task."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "execution-loop"
sys.path.insert(0, str(REPOSITORY_DIR))

from execution_loop_repository import ExecutionLoopBuilderError, ExecutionLoopRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Register an execution loop task")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        result = ExecutionLoopRepository().register_loop_task(
            spec_path=Path(args.spec),
            execute=args.execute,
        )
    except ExecutionLoopBuilderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
