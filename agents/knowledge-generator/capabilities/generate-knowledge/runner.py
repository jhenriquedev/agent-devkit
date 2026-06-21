#!/usr/bin/env python3
"""Runner for knowledge-generator/generate-knowledge."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infra" / "integrations" / "local-source"))

from knowledge_repository import KnowledgeGeneratorError, KnowledgeRepository  # pylint: disable=import-error


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate profile-driven knowledge")
    parser.add_argument("--source", required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--profile", default="auto")
    parser.add_argument("--project-id")
    parser.add_argument("--yes-create-dir", action="store_true")
    parser.add_argument("--yes-overwrite", action="store_true")
    args = parser.parse_args()

    try:
        result = KnowledgeRepository().generate_knowledge(
            source=args.source,
            output_dir=args.output_dir,
            profile=args.profile,
            project_id=args.project_id,
            yes_create_dir=args.yes_create_dir,
            yes_overwrite=args.yes_overwrite,
        )
    except KnowledgeGeneratorError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
