#!/usr/bin/env python3
"""Delegate Claude Code plugin capability execution to agent run."""

from __future__ import annotations

import sys

from runtime import run_agent


def main() -> int:
    args = list(sys.argv[1:])
    global_flags = []
    if "--json" in args:
        global_flags.append("--json")
        args = [arg for arg in args if arg != "--json"]
    return run_agent(__file__, [*global_flags, "run", *args])


if __name__ == "__main__":
    raise SystemExit(main())
