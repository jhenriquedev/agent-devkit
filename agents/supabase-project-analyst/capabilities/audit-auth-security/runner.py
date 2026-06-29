#!/usr/bin/env python3
"""Runner for supabase-project-analyst/audit-auth-security."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "supabase-project"
sys.path.insert(0, str(REPOSITORY_DIR))

from supabase_project_repository import SupabaseProjectError, SupabaseProjectRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Supabase Auth security")
    parser.add_argument("--project-path", default=".")
    args = parser.parse_args()
    try:
        result = SupabaseProjectRepository().audit_auth_security(project_path=Path(args.project_path))
    except SupabaseProjectError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
