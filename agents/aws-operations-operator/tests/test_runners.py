#!/usr/bin/env python3
"""Runner tests for aws-operations-operator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


class AwsOperationsOperatorRunnerTest(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
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
