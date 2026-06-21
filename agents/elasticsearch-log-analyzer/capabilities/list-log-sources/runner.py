#!/usr/bin/env python3
"""Runner for list-log-sources."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import get_repository, load_fixture, print_error, value_or_dash, write_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run elasticsearch-log-analyzer/list-log-sources")
    parser.add_argument("--pattern")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = load_fixture(args.fixture) if args.fixture else get_repository().list_sources(pattern=args.pattern, limit=args.limit)
        write_output(render(payload), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render(payload: dict) -> str:
    lines = ["# Elasticsearch Log Sources", "", f"- Pattern: {value_or_dash(payload.get('pattern'))}", ""]
    lines.extend(render_named_items("Indices", payload.get("indices") or [], "index"))
    lines.extend(render_named_items("Data Streams", payload.get("data_streams") or [], "name"))
    lines.extend(render_named_items("Aliases", payload.get("aliases") or [], "alias"))
    return "\n".join(lines).rstrip() + "\n"


def render_named_items(title: str, items: list[dict], key: str) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.append("- None.")
    for item in items:
        lines.append(f"- {value_or_dash(item.get(key))}")
    lines.append("")
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
