#!/usr/bin/env python3
"""Tests for AWS architecture repository."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


AWS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AWS_DIR))

from aws_repository import AwsArchitectureConfig, AwsArchitectureRepository, AwsArchitectureRepositoryError  # noqa: E402
from dependency_mapper import build_dependency_map  # noqa: E402
from normalizers import normalize_lambda_function, service_counts  # noqa: E402


class AwsArchitectureRepositoryTest(unittest.TestCase):
    def test_blocks_commands_outside_allowlist(self) -> None:
        repo = AwsArchitectureRepository(AwsArchitectureConfig(default_region="us-east-1"))

        with self.assertRaises(AwsArchitectureRepositoryError):
            repo.aws_json(["s3api", "delete-bucket", "--bucket", "example"], region="us-east-1")

    def test_builds_aws_cli_command_with_region_and_profile(self) -> None:
        config = AwsArchitectureConfig(default_region="us-east-1", profile="dev")
        repo = AwsArchitectureRepository(config)

        command = repo.build_aws_command(["lambda", "list-functions"], region=None)

        self.assertEqual(command[:4], ["aws", "lambda", "list-functions", "--region"])
        self.assertIn("us-east-1", command)
        self.assertEqual(command[-4:], ["--output", "json", "--profile", "dev"])

    def test_normalizes_lambda_function_resource(self) -> None:
        resource = normalize_lambda_function(
            {
                "FunctionArn": "arn:aws:lambda:us-east-1:123:function:orders",
                "FunctionName": "orders",
                "Runtime": "python3.12",
                "Role": "arn:aws:iam::123:role/orders-role",
            },
            account_id="123",
            region="us-east-1",
        )

        self.assertEqual(resource["service"], "lambda")
        self.assertEqual(resource["relationships"][0]["type"], "uses-role")

    def test_dependency_map_uses_resource_relationships(self) -> None:
        resources = [
            {
                "id": "lambda-1",
                "name": "worker",
                "service": "lambda",
                "relationships": [{"target_id": "role-1", "type": "uses-role", "confidence": "confirmed"}],
            },
            {"id": "role-1", "name": "worker-role", "service": "iam", "relationships": []},
        ]

        result = build_dependency_map(resources)

        self.assertEqual(result["edge_count"], 1)
        self.assertEqual(result["edges"][0]["target_id"], "role-1")

    def test_counts_services(self) -> None:
        self.assertEqual(service_counts([{"service": "lambda"}, {"service": "sqs"}, {"service": "lambda"}]), {"lambda": 2, "sqs": 1})


if __name__ == "__main__":
    unittest.main()
