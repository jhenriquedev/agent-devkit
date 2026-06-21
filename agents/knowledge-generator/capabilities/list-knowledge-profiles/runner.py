#!/usr/bin/env python3
"""Runner for knowledge-generator/list-knowledge-profiles."""

from __future__ import annotations

import json
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infra" / "integrations" / "local-source"))

from knowledge_repository import KnowledgeRepository  # pylint: disable=import-error


def main() -> int:
    print(json.dumps(KnowledgeRepository().list_profiles(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
