#!/usr/bin/env python3
"""Runner for pyautogui-automation-builder/plan-desktop-automation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "pyautogui-automation"
sys.path.insert(0, str(REPOSITORY_DIR))

from pyautogui_automation_repository import PyAutoGUIAutomationError, PyAutoGUIAutomationRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a PyAutoGUI desktop automation")
    parser.add_argument("--spec", required=True)
    args = parser.parse_args()

    try:
        result = PyAutoGUIAutomationRepository().plan_desktop_automation(spec_path=Path(args.spec))
    except PyAutoGUIAutomationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
