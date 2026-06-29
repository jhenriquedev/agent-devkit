#!/usr/bin/env python3
"""Runner for execution-loop-builder/review-loop-safety."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "execution-loop"
sys.path.insert(0, str(REPOSITORY_DIR))

from execution_loop_repository import ExecutionLoopBuilderError, ExecutionLoopRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Review execution loop safety")
    parser.add_argument("--spec")
    parser.add_argument("--text")
    args = parser.parse_args()
    if not args.spec and not args.text:
        print("one of --spec or --text is required", file=sys.stderr)
        return 2
    try:
        result = ExecutionLoopRepository().review_loop_safety(
            spec_path=Path(args.spec) if args.spec else None,
            text=args.text,
        )
    except ExecutionLoopBuilderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
