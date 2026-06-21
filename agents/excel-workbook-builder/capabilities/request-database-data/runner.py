#!/usr/bin/env python3
"""Runner for excel-workbook-builder/request-database-data."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ALLOWED_AGENTS = {
    "sqlserver-data-analyzer",
    "postgres-data-analyzer",
    "azure-devops-orchestrator",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a delegated data request")
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--capability-id", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--expected-schema", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        if args.agent_id not in ALLOWED_AGENTS:
            raise ValueError(f"unsupported delegated agent: {args.agent_id}")
        markdown = "\n".join(
            [
                "# Delegated Data Request",
                "",
                f"- Agent: {args.agent_id}",
                f"- Capability: {args.capability_id}",
                f"- Expected schema: {args.expected_schema}",
                "",
                "## Request",
                "",
                args.request,
                "",
                "## Execution Policy",
                "",
                "- Execute as read-only.",
                "- Return normalized JSON or CSV.",
                "- Do not mutate source systems.",
            ]
        ).rstrip() + "\n"
        if args.output:
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown, encoding="utf-8")
        else:
            print(markdown)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

