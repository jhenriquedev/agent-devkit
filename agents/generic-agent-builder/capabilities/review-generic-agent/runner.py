#!/usr/bin/env python3
"""Runner for generic-agent-builder/review-generic-agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "generic-agent"
sys.path.insert(0, str(REPOSITORY_DIR))

from generic_agent_repository import GenericAgentError, GenericAgentRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Review portable generic agent instructions")
    parser.add_argument("--input")
    parser.add_argument("--text")
    parser.add_argument("--target-host", default="generic")
    args = parser.parse_args()

    if not args.input and not args.text:
        print("one of --input or --text is required", file=sys.stderr)
        return 2

    try:
        text = Path(args.input).read_text(encoding="utf-8") if args.input else str(args.text)
        result = GenericAgentRepository().review_generic_agent(text=text, target_host=args.target_host)
    except (GenericAgentError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
