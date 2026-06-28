#!/usr/bin/env python3
"""Delegate Codex plugin diagnostics to agent doctor."""

from __future__ import annotations

import sys

from runtime import run_agent


def main() -> int:
    return run_agent(__file__, [*sys.argv[1:], "doctor"])


if __name__ == "__main__":
    raise SystemExit(main())
