#!/usr/bin/env python3
"""Runner for excel-workbook-builder/request-database-data."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
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
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--ai-devkit", default="./ai-devkit")
    parser.add_argument("--result-output")
    parser.add_argument("--output")
    parser.add_argument("delegated_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    try:
        if args.agent_id not in ALLOWED_AGENTS:
            raise ValueError(f"unsupported delegated agent: {args.agent_id}")
        if args.execute:
            command = [
                args.ai_devkit,
                "run",
                args.agent_id,
                args.capability_id,
                *args.delegated_args,
            ]
            result = subprocess.run(
                command,
                cwd=Path.cwd(),
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if result.returncode != 0:
                raise ValueError(result.stderr.strip() or result.stdout.strip() or "delegated agent failed")
            if args.result_output:
                output = Path(args.result_output).expanduser().resolve()
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(result.stdout, encoding="utf-8")
            else:
                print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
            return 0
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
