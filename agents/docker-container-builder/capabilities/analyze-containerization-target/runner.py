#!/usr/bin/env python3
"""Runner for docker-container-builder/analyze-containerization-target."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "docker-container"
sys.path.insert(0, str(REPOSITORY_DIR))

from docker_container_repository import DockerContainerBuilderError, DockerContainerRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a local project for Docker containerization")
    parser.add_argument("--project-path", required=True)
    args = parser.parse_args()
    try:
        result = DockerContainerRepository().analyze_containerization_target(project_path=Path(args.project_path))
    except DockerContainerBuilderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
