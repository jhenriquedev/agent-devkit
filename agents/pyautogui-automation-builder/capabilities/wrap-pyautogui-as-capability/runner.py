#!/usr/bin/env python3
"""Runner for pyautogui-automation-builder/wrap-pyautogui-as-capability."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "pyautogui-automation"
sys.path.insert(0, str(REPOSITORY_DIR))

from pyautogui_automation_repository import PyAutoGUIAutomationError, PyAutoGUIAutomationRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Wrap a PyAutoGUI automation as an Agent DevKit capability")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--capability-id", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-overwrite", action="store_true")
    args = parser.parse_args()

    try:
        result = PyAutoGUIAutomationRepository().wrap_pyautogui_as_capability(
            spec_path=Path(args.spec),
            agent_id=args.agent_id,
            capability_id=args.capability_id,
            execute=args.execute,
            allow_overwrite=args.allow_overwrite,
        )
    except PyAutoGUIAutomationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
