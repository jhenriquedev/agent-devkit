#!/usr/bin/env python3
"""Runner for docker-container-builder/review-docker-security."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "docker-container"
sys.path.insert(0, str(REPOSITORY_DIR))

from docker_container_repository import DockerContainerBuilderError, DockerContainerRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Review Docker artifacts")
    parser.add_argument("--dockerfile")
    parser.add_argument("--compose")
    parser.add_argument("--dockerfile-text")
    parser.add_argument("--compose-text")
    args = parser.parse_args()
    if not any((args.dockerfile, args.compose, args.dockerfile_text, args.compose_text)):
        print("one of --dockerfile, --compose, --dockerfile-text or --compose-text is required", file=sys.stderr)
        return 2
    try:
        result = DockerContainerRepository().review_docker_security(
            dockerfile_path=Path(args.dockerfile) if args.dockerfile else None,
            compose_path=Path(args.compose) if args.compose else None,
            dockerfile_text=args.dockerfile_text,
            compose_text=args.compose_text,
        )
    except (DockerContainerBuilderError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
