#!/usr/bin/env python3
"""Runner for automation-architect/review-automation-solution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "automation-architecture"
sys.path.insert(0, str(REPOSITORY_DIR))

from automation_architecture_repository import AutomationArchitectureError, AutomationArchitectureRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Review an automation solution")
    parser.add_argument("--request")
    parser.add_argument("--spec")
    parser.add_argument("--solution")
    args = parser.parse_args()

    try:
        result = AutomationArchitectureRepository().review_automation_solution(
            request=args.request,
            spec_path=Path(args.spec) if args.spec else None,
            solution=args.solution,
        )
    except AutomationArchitectureError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
