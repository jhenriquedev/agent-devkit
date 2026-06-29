#!/usr/bin/env python3
"""Runner for playwright-automation-builder/review-playwright-artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "playwright-automation"
sys.path.insert(0, str(REPOSITORY_DIR))

from playwright_automation_repository import PlaywrightAutomationRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Review Playwright artifacts")
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--script")
    args = parser.parse_args()
    text = Path(args.script).read_text(encoding="utf-8") if args.script else None
    result = PlaywrightAutomationRepository().review_playwright_artifacts(
        paths=[Path(item) for item in args.artifact],
        text=text,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
