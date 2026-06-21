#!/usr/bin/env python3
"""Runner for n2-support-agent/generate-patch-plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import build_contract, print_error, write_output  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run n2-support-agent/generate-patch-plan")
    parser.add_argument("--project")
    parser.add_argument("--card", type=int)
    parser.add_argument("--n1-contract")
    parser.add_argument("--codebase-path")
    parser.add_argument("--output")
    parser.add_argument("--fixture")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    try:
        contract, markdown = build_contract(args)
        payload = {
            "patchPlan": contract["patchPlan"],
            "rootCause": contract["rootCause"],
            "codeAnalysis": contract["codeAnalysis"],
        }
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else markdown
        write_output(content, None if args.output else None)
    except Exception as exc:
        return print_error(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
