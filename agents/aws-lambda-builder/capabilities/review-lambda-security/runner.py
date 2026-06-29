#!/usr/bin/env python3
"""Runner for aws-lambda-builder/review-lambda-security."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "infra" / "integrations" / "aws-lambda"
sys.path.insert(0, str(REPOSITORY_DIR))

from aws_lambda_repository import AwsLambdaBuilderError, AwsLambdaRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Review AWS Lambda security")
    parser.add_argument("--spec", required=True)
    args = parser.parse_args()

    try:
        result = AwsLambdaRepository().review_lambda_security(spec_path=Path(args.spec))
    except AwsLambdaBuilderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
