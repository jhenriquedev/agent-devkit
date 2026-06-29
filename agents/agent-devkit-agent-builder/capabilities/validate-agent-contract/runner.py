#!/usr/bin/env python3
"""Runner for agent-devkit-agent-builder/validate-agent-contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "agent-devkit"
sys.path.insert(0, str(REPOSITORY_DIR))

from agent_builder_repository import AgentBuilderRepository, AgentBuilderError  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an internal Agent DevKit agent scaffold")
    parser.add_argument("--agent-id", required=True)
    args = parser.parse_args()

    try:
        result = AgentBuilderRepository().validate_agent_contract(agent_id=args.agent_id)
    except AgentBuilderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
