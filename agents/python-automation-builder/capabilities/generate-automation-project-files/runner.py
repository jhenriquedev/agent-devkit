#!/usr/bin/env python3
"""Runner for python-automation-builder/generate-automation-project-files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "python-automation"
sys.path.insert(0, str(REPOSITORY_DIR))

from python_automation_repository import PythonAutomationError, PythonAutomationRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Python automation project files")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-overwrite", action="store_true")
    args = parser.parse_args()

    try:
        result = PythonAutomationRepository().generate_automation_project_files(
            spec_path=Path(args.spec),
            execute=args.execute,
            allow_overwrite=args.allow_overwrite,
        )
    except PythonAutomationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
