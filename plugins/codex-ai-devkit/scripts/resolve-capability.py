#!/usr/bin/env python3
"""List AI DevKit capabilities for host-side routing."""

from __future__ import annotations

import sys

from runtime import run_agent


def main() -> int:
    return run_agent(__file__, ["--json", "capabilities", "list", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
