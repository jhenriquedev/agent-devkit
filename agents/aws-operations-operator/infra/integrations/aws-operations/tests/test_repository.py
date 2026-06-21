#!/usr/bin/env python3
"""Tests for AWS operations repository."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


AWS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AWS_DIR))

from aws_operations_repository import (  # noqa: E402
    AwsOperation,
    AwsOperationsConfig,
    AwsOperationsRepository,
    AwsOperationsRepositoryError,
)


class AwsOperationsRepositoryTest(unittest.TestCase):
    def test_builds_force_ecs_deployment_operation(self) -> None:
        operation = AwsOperation.force_ecs_deployment(cluster="orders", service="orders-api")

        self.assertEqual(operation.operation, "force-ecs-deployment")
        self.assertEqual(operation.resource_id, "orders/orders-api")
        self.assertEqual(operation.args[:2], ["ecs", "update-service"])

    def test_dry_run_does_not_execute(self) -> None:
        repo = AwsOperationsRepository(AwsOperationsConfig(default_region="us-east-1", profile="dev"))
        operation = AwsOperation.force_ecs_deployment(cluster="orders", service="orders-api")

        result = repo.run_operation(operation, environment="dev", execute=False, confirm_resource=None)

        self.assertEqual(result["status"], "planned")
        self.assertFalse(result["execute"])
        self.assertIn("--profile", result["aws_command"])

    def test_execute_requires_confirm_resource(self) -> None:
        repo = AwsOperationsRepository(AwsOperationsConfig(default_region="us-east-1"))
        operation = AwsOperation.force_ecs_deployment(cluster="orders", service="orders-api")

        with self.assertRaises(AwsOperationsRepositoryError):
            repo.run_operation(operation, environment="dev", execute=True, confirm_resource=None)

    def test_prod_execute_requires_prd_environment(self) -> None:
        repo = AwsOperationsRepository(AwsOperationsConfig(default_region="us-east-1"))
        operation = AwsOperation.force_ecs_deployment(cluster="orders", service="orders-api")

        with self.assertRaises(AwsOperationsRepositoryError):
            repo.run_operation(operation, environment="prod", execute=True, confirm_resource=operation.resource_id)

    def test_blocks_unknown_operation_command(self) -> None:
        repo = AwsOperationsRepository(AwsOperationsConfig(default_region="us-east-1"))
        operation = AwsOperation(operation="bad", resource_id="x", args=["s3api", "delete-bucket", "--bucket", "x"])

        with self.assertRaises(AwsOperationsRepositoryError):
            repo.run_operation(operation, environment="dev", execute=False, confirm_resource=None)


if __name__ == "__main__":
    unittest.main()
