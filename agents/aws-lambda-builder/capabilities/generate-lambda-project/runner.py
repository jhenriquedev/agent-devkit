#!/usr/bin/env python3
"""Runner for aws-lambda-builder/generate-lambda-project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "aws-lambda"
sys.path.insert(0, str(REPOSITORY_DIR))

from aws_lambda_repository import AwsLambdaBuilderError, AwsLambdaRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an AWS Lambda project")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-overwrite", action="store_true")
    args = parser.parse_args()

    try:
        result = AwsLambdaRepository().generate_lambda_project(
            spec_path=Path(args.spec),
            execute=args.execute,
            allow_overwrite=args.allow_overwrite,
        )
    except AwsLambdaBuilderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
