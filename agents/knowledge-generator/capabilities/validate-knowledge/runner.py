#!/usr/bin/env python3
"""Runner for knowledge-generator/validate-knowledge."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infra" / "integrations" / "local-source"))

from knowledge_repository import KnowledgeRepository  # pylint: disable=import-error


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated knowledge")
    parser.add_argument("--knowledge-dir", required=True)
    args = parser.parse_args()

    result = KnowledgeRepository().validate_knowledge(knowledge_dir=args.knowledge_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
