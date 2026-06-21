#!/usr/bin/env python3
"""Runner for plan-migration."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import get_repository, load_fixture, print_error, render_plan, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run database-change-operator/plan-migration")
    parser.add_argument("--path", required=True)
    parser.add_argument("--database")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        plan = load_fixture(args.fixture) if args.fixture else get_repository(args.database).plan_migration(path=args.path)
        if args.fixture and args.database:
            plan.setdefault("database", args.database)
        lines = ["# Migration Plan", ""]
        lines.extend(render_plan(plan))
        write_output("\n".join(lines).rstrip() + "\n", args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
