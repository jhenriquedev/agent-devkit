#!/usr/bin/env python3
"""Runner tests for aws-operations-operator."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


class AwsOperationsOperatorRunnerTest(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        for key in list(env):
            if key.startswith("AWS_OPERATIONS_ALLOWED_ACCOUNTS_") or key.startswith("AWS_OPERATIONS_DEFAULT_REGION_"):
                env.pop(key)
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

    def test_agent_is_discoverable(self) -> None:
        result = self.run_cli("--json", "agents")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        agents = {item["id"] for item in payload["items"]}
        self.assertIn("aws-operations-operator", agents)

    def test_plan_operational_action_writes_plan_and_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "plan-operational-action",
                "--operation",
                "force-ecs-deployment",
                "--resource-id",
                "cluster/orders-service",
                "--environment",
                "dev",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            plan = (output_dir / "operation-plan.md").read_text(encoding="utf-8")
            dry_run = json.loads((output_dir / "operation-dry-run.json").read_text(encoding="utf-8"))

        self.assertIn("force-ecs-deployment", plan)
        self.assertFalse(dry_run["execute"])
        self.assertEqual(dry_run["status"], "planned")

    def test_force_ecs_deployment_defaults_to_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "force-ecs-deployment",
                "--cluster",
                "orders",
                "--service",
                "orders-api",
                "--environment",
                "dev",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            dry_run = json.loads((output_dir / "operation-dry-run.json").read_text(encoding="utf-8"))

        self.assertEqual(dry_run["operation"], "force-ecs-deployment")
        self.assertEqual(dry_run["aws_command"][:3], ["aws", "ecs", "update-service"])
        self.assertFalse((output_dir / "operation-result.json").exists())

    def test_restart_ecs_service_keeps_restart_operation_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "restart-ecs-service",
                "--cluster",
                "orders",
                "--service",
                "orders-api",
                "--environment",
                "dev",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            dry_run = json.loads((output_dir / "operation-dry-run.json").read_text(encoding="utf-8"))

        self.assertEqual(dry_run["operation"], "restart-ecs-service")
        self.assertEqual(dry_run["aws_command"][:3], ["aws", "ecs", "update-service"])

    def test_plan_operational_action_rejects_unknown_operation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "plan-operational-action",
                "--operation",
                "delete-rds",
                "--resource-id",
                "prod-db",
                "--environment",
                "prd",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not allowed", result.stderr.lower())

    def test_lambda_payload_is_redacted_in_dry_run_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "invoke-lambda",
                "--function-name",
                "reconcile-orders",
                "--payload",
                '{"secret":"abc"}',
                "--environment",
                "dev",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            artifact = (output_dir / "operation-dry-run.json").read_text(encoding="utf-8")
            plan = (output_dir / "operation-plan.md").read_text(encoding="utf-8")

        self.assertNotIn("abc", artifact)
        self.assertNotIn("abc", plan)
        self.assertIn("<redacted", artifact)

    def test_cloudfront_asg_and_eventbridge_generate_dry_run_artifacts(self) -> None:
        scenarios = [
            (
                "invalidate-cloudfront-cache",
                ["--distribution-id", "E123456", "--paths", "/index.html /static/*"],
                "invalidate-cloudfront-cache",
            ),
            (
                "scale-autoscaling-group",
                ["--auto-scaling-group", "orders-asg", "--desired-capacity", "3"],
                "scale-autoscaling-group",
            ),
            (
                "toggle-eventbridge-rule",
                ["--rule-name", "nightly-orders", "--action", "disable"],
                "toggle-eventbridge-rule",
            ),
        ]
        for capability, capability_args, expected_operation in scenarios:
            with self.subTest(capability=capability), tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir) / "out"

                result = self.run_cli(
                    "run",
                    "aws-operations-operator",
                    capability,
                    *capability_args,
                    "--environment",
                    "dev",
                    "--output-dir",
                    str(output_dir),
                    "--yes-create-dir",
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                dry_run = json.loads((output_dir / "operation-dry-run.json").read_text(encoding="utf-8"))

            self.assertEqual(dry_run["operation"], expected_operation)
            self.assertEqual(dry_run["status"], "planned")
            self.assertFalse(dry_run["execute"])

    def test_sqs_destructive_capabilities_are_blocked_plan_only(self) -> None:
        scenarios = [
            (
                "redrive-sqs-dlq",
                [
                    "--source-arn",
                    "arn:aws:sqs:us-east-1:123456789012:orders-dlq",
                    "--destination-arn",
                    "arn:aws:sqs:us-east-1:123456789012:orders",
                ],
            ),
            (
                "purge-sqs-queue-plan",
                ["--queue-url", "https://sqs.us-east-1.amazonaws.com/123456789012/orders"],
            ),
        ]
        for capability, capability_args in scenarios:
            with self.subTest(capability=capability), tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir) / "out"

                result = self.run_cli(
                    "run",
                    "aws-operations-operator",
                    capability,
                    *capability_args,
                    "--environment",
                    "dev",
                    "--output-dir",
                    str(output_dir),
                    "--yes-create-dir",
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                dry_run = json.loads((output_dir / "operation-dry-run.json").read_text(encoding="utf-8"))

            self.assertEqual(dry_run["status"], "blocked-plan-only")
            self.assertTrue(dry_run["destructive"])

    def test_execute_requires_confirm_resource(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "force-ecs-deployment",
                "--cluster",
                "orders",
                "--service",
                "orders-api",
                "--environment",
                "dev",
                "--execute",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("confirm", result.stderr.lower())

    def test_execute_requires_account_allowlist_even_with_confirm_resource(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "force-ecs-deployment",
                "--cluster",
                "orders",
                "--service",
                "orders-api",
                "--environment",
                "dev",
                "--execute",
                "--confirm-resource",
                "orders/orders-api",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("allowed aws accounts", result.stderr.lower())

    def test_generate_operation_report_reads_operation_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"
            output_dir.mkdir()
            (output_dir / "operation-dry-run.json").write_text(
                json.dumps({"operation": "force-ecs-deployment", "status": "planned", "execute": False}),
                encoding="utf-8",
            )

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "generate-operation-report",
                "--operation-dir",
                str(output_dir),
                "--output-dir",
                str(output_dir),
                "--yes-overwrite",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = (output_dir / "operation-report.md").read_text(encoding="utf-8")

        self.assertIn("force-ecs-deployment", report)


if __name__ == "__main__":
    unittest.main()
