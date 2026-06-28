#!/usr/bin/env python3
"""Delegate Codex plugin runtime installation to agent install."""

from __future__ import annotations

import sys

from runtime import run_agent


def main() -> int:
    args = list(sys.argv[1:])
    return run_agent(__file__, ["install", *args, "--host", "codex"])


if __name__ == "__main__":
    raise SystemExit(main())
