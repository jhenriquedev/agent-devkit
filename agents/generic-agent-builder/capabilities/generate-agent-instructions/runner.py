#!/usr/bin/env python3
"""Runner for generic-agent-builder/generate-agent-instructions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "generic-agent"
sys.path.insert(0, str(REPOSITORY_DIR))

from generic_agent_repository import GenericAgentError, GenericAgentRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate portable generic agent instructions")
    parser.add_argument("--spec", required=True)
    args = parser.parse_args()

    try:
        result = GenericAgentRepository().generate_agent_instructions(spec_path=Path(args.spec))
    except GenericAgentError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
