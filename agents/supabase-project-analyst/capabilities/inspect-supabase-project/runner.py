#!/usr/bin/env python3
"""Runner for supabase-project-analyst/inspect-supabase-project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "supabase-project"
sys.path.insert(0, str(REPOSITORY_DIR))

from supabase_project_repository import SupabaseProjectError, SupabaseProjectRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a local Supabase project")
    parser.add_argument("--project-path", default=".")
    parser.add_argument("--include-cli-status", action="store_true")
    args = parser.parse_args()
    try:
        result = SupabaseProjectRepository().inspect_supabase_project(
            project_path=Path(args.project_path),
            include_cli_status=args.include_cli_status,
        )
    except SupabaseProjectError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
