#!/usr/bin/env python3
"""Tests for AWS operations repository."""

from __future__ import annotations

import sys
import unittest
from subprocess import CompletedProcess
from pathlib import Path
from unittest.mock import patch


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

    def test_lambda_payload_is_redacted_from_artifacts(self) -> None:
        repo = AwsOperationsRepository(AwsOperationsConfig(default_region="us-east-1"))
        operation = AwsOperation.invoke_lambda(function_name="reconcile-orders", payload='{"secret":"abc"}')

        result = repo.run_operation(operation, environment="dev", execute=False, confirm_resource=None)
        serialized = str(result)

        self.assertNotIn("abc", serialized)
        self.assertIn("<redacted", " ".join(result["aws_command"]))

    def test_restart_ecs_has_own_operation_identity(self) -> None:
        operation = AwsOperation.restart_ecs_service(cluster="orders", service="orders-api")

        self.assertEqual(operation.operation, "restart-ecs-service")
        self.assertEqual(operation.resource_id, "orders/orders-api")
        self.assertEqual(operation.args[:2], ["ecs", "update-service"])

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

    def test_production_alias_execute_requires_prd_environment(self) -> None:
        repo = AwsOperationsRepository(AwsOperationsConfig(default_region="us-east-1"))
        operation = AwsOperation.force_ecs_deployment(cluster="orders", service="orders-api")

        with self.assertRaises(AwsOperationsRepositoryError):
            repo.run_operation(operation, environment="production", execute=True, confirm_resource=operation.resource_id)

    def test_execute_requires_allowed_account_for_environment(self) -> None:
        repo = AwsOperationsRepository(
            AwsOperationsConfig(default_region="us-east-1", allowed_accounts={"prd": {"111111111111"}})
        )
        operation = AwsOperation.force_ecs_deployment(cluster="orders", service="orders-api")

        with patch("aws_operations_repository.subprocess.run") as run:
            run.return_value = CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"Account":"222222222222","Arn":"arn:aws:iam::222222222222:user/operator","UserId":"AID"}',
                stderr="",
            )

            with self.assertRaises(AwsOperationsRepositoryError):
                repo.run_operation(operation, environment="prd", execute=True, confirm_resource=operation.resource_id)

    def test_execute_captures_preflight_postcheck_and_lambda_result_file(self) -> None:
        repo = AwsOperationsRepository(
            AwsOperationsConfig(default_region="us-east-1", allowed_accounts={"dev": {"111111111111"}})
        )
        operation = AwsOperation.invoke_lambda(function_name="reconcile-orders", payload='{"secret":"abc"}')

        def fake_run(command, **_kwargs):
            if command[1:3] == ["sts", "get-caller-identity"]:
                return CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout='{"Account":"111111111111","Arn":"arn:aws:iam::111111111111:user/operator","UserId":"AID"}',
                    stderr="",
                )
            if command[1:3] == ["lambda", "get-function-configuration"]:
                return CompletedProcess(args=command, returncode=0, stdout='{"State":"Active"}', stderr="")
            if command[1:3] == ["lambda", "invoke"]:
                output_path = next(part for part in command if part.endswith("lambda-output.json"))
                Path(output_path).write_text('{"ok":true,"token":"secret-value"}', encoding="utf-8")
                return CompletedProcess(args=command, returncode=0, stdout='{"StatusCode":200}', stderr="")
            raise AssertionError(f"unexpected command: {command}")

        with patch("aws_operations_repository.subprocess.run", side_effect=fake_run):
            result = repo.run_operation(operation, environment="dev", execute=True, confirm_resource=operation.resource_id)

        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["account_validation"]["account_id"], "111111111111")
        self.assertEqual(result["preflight"]["kind"], "lambda")
        self.assertEqual(result["post_check"]["kind"], "lambda")
        self.assertEqual(len(result["lambda_response"]["payload_hash"]), 64)
        self.assertGreater(result["lambda_response"]["payload_bytes"], 0)
        self.assertNotIn("secret-value", str(result))

    def test_execute_collects_ecs_preflight_and_postcheck(self) -> None:
        repo = AwsOperationsRepository(
            AwsOperationsConfig(default_region="us-east-1", allowed_accounts={"dev": {"111111111111"}})
        )
        operation = AwsOperation.force_ecs_deployment(cluster="orders", service="orders-api")
        observed = []

        def fake_run(command, **_kwargs):
            observed.append(command[1:3])
            if command[1:3] == ["sts", "get-caller-identity"]:
                return CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout='{"Account":"111111111111","Arn":"arn:aws:iam::111111111111:user/operator","UserId":"AID"}',
                    stderr="",
                )
            if command[1:3] == ["ecs", "describe-services"]:
                return CompletedProcess(args=command, returncode=0, stdout='{"services":[{"status":"ACTIVE"}]}', stderr="")
            if command[1:3] == ["ecs", "update-service"]:
                return CompletedProcess(args=command, returncode=0, stdout='{"service":{"status":"ACTIVE"}}', stderr="")
            raise AssertionError(f"unexpected command: {command}")

        with patch("aws_operations_repository.subprocess.run", side_effect=fake_run):
            result = repo.run_operation(operation, environment="dev", execute=True, confirm_resource=operation.resource_id)

        self.assertEqual(result["preflight"]["kind"], "ecs")
        self.assertEqual(result["post_check"]["kind"], "ecs")
        self.assertEqual(
            observed,
            [
                ["sts", "get-caller-identity"],
                ["ecs", "describe-services"],
                ["ecs", "update-service"],
                ["ecs", "describe-services"],
            ],
        )

    def test_blocks_unknown_operation_command(self) -> None:
        repo = AwsOperationsRepository(AwsOperationsConfig(default_region="us-east-1"))
        operation = AwsOperation(operation="bad", resource_id="x", args=["s3api", "delete-bucket", "--bucket", "x"])

        with self.assertRaises(AwsOperationsRepositoryError):
            repo.run_operation(operation, environment="dev", execute=False, confirm_resource=None)


if __name__ == "__main__":
    unittest.main()
