#!/usr/bin/env python3
"""Runner for agent-devkit-agent-builder/plan-agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "agent-devkit"
sys.path.insert(0, str(REPOSITORY_DIR))

from agent_builder_repository import AgentBuilderRepository, AgentBuilderError  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a new internal Agent DevKit agent")
    parser.add_argument("--spec", required=True)
    args = parser.parse_args()

    try:
        result = AgentBuilderRepository().plan_agent(spec_path=Path(args.spec))
    except AgentBuilderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
