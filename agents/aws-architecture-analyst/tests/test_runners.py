#!/usr/bin/env python3
"""Runner tests for aws-architecture-analyst."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


def sample_fixture() -> dict:
    return {
        "account_id": "123456789012",
        "region": "us-east-1",
        "resources": [
            {
                "id": "arn:aws:lambda:us-east-1:123456789012:function:orders-worker",
                "arn": "arn:aws:lambda:us-east-1:123456789012:function:orders-worker",
                "name": "orders-worker",
                "service": "lambda",
                "resource_type": "function",
                "region": "us-east-1",
                "account_id": "123456789012",
                "relationships": [
                    {
                        "target_id": "arn:aws:iam::123456789012:role/orders-worker-role",
                        "type": "uses-role",
                        "confidence": "confirmed",
                    }
                ],
                "attributes": {"runtime": "python3.12", "vpc_attached": True},
            },
            {
                "id": "arn:aws:iam::123456789012:role/orders-worker-role",
                "arn": "arn:aws:iam::123456789012:role/orders-worker-role",
                "name": "orders-worker-role",
                "service": "iam",
                "resource_type": "role",
                "region": "global",
                "account_id": "123456789012",
                "relationships": [],
                "attributes": {},
            },
            {
                "id": "arn:aws:sqs:us-east-1:123456789012:orders-dlq",
                "arn": "arn:aws:sqs:us-east-1:123456789012:orders-dlq",
                "name": "orders-dlq",
                "service": "sqs",
                "resource_type": "queue",
                "region": "us-east-1",
                "account_id": "123456789012",
                "relationships": [],
                "attributes": {"has_dlq": False},
            },
        ],
    }


class AwsArchitectureAnalystRunnerTest(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def parse_runner_payload(self, result: subprocess.CompletedProcess[str]) -> dict:
        payload = json.loads(result.stdout)
        if "stdout" in payload:
            return json.loads(payload["stdout"])
        return payload

    def test_agent_is_discoverable(self) -> None:
        result = self.run_cli("--json", "agents")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        agents = {item["id"] for item in payload["items"]}
        self.assertIn("aws-architecture-analyst", agents)

    def test_discover_account_inventory_writes_artifacts_from_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "inventory-fixture.json"
            output_dir = Path(tmpdir) / "out"
            fixture.write_text(json.dumps(sample_fixture()), encoding="utf-8")

            result = self.run_cli(
                "run",
                "aws-architecture-analyst",
                "discover-account-inventory",
                "--fixture",
                str(fixture),
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output_dir / "inventory.json").exists())
            self.assertTrue((output_dir / "inventory-summary.md").exists())
            self.assertTrue((output_dir / "collection-metadata.json").exists())
            inventory = json.loads((output_dir / "inventory.json").read_text(encoding="utf-8"))

        self.assertEqual(inventory["resource_count"], 3)
        self.assertEqual(inventory["services"]["lambda"], 1)

    def test_map_service_dependencies_writes_dependency_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            inventory = Path(tmpdir) / "inventory.json"
            output_dir = Path(tmpdir) / "out"
            payload = sample_fixture()
            payload["resource_count"] = len(payload["resources"])
            payload["services"] = {"lambda": 1, "iam": 1, "sqs": 1}
            inventory.write_text(json.dumps(payload), encoding="utf-8")

            result = self.run_cli(
                "run",
                "aws-architecture-analyst",
                "map-service-dependencies",
                "--inventory",
                str(inventory),
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            dependency_map = json.loads((output_dir / "dependency-map.json").read_text(encoding="utf-8"))

        self.assertEqual(dependency_map["edge_count"], 1)
        self.assertEqual(dependency_map["edges"][0]["type"], "uses-role")

    def test_generate_architecture_report_uses_inventory_and_dependency_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            inventory = Path(tmpdir) / "inventory.json"
            dependency_map = Path(tmpdir) / "dependency-map.json"
            output_dir = Path(tmpdir) / "out"
            payload = sample_fixture()
            payload["resource_count"] = len(payload["resources"])
            payload["services"] = {"lambda": 1, "iam": 1, "sqs": 1}
            inventory.write_text(json.dumps(payload), encoding="utf-8")
            dependency_map.write_text(
                json.dumps(
                    {
                        "nodes": payload["resources"],
                        "edges": [
                            {
                                "source_id": payload["resources"][0]["id"],
                                "target_id": payload["resources"][1]["id"],
                                "type": "uses-role",
                                "confidence": "confirmed",
                            }
                        ],
                        "edge_count": 1,
                    }
                ),
                encoding="utf-8",
            )

            result = self.run_cli(
                "run",
                "aws-architecture-analyst",
                "generate-architecture-report",
                "--inventory",
                str(inventory),
                "--dependency-map",
                str(dependency_map),
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = (output_dir / "architecture-report.md").read_text(encoding="utf-8")

        self.assertIn("orders-worker", report)
        self.assertIn("uses-role", report)


if __name__ == "__main__":
    unittest.main()
