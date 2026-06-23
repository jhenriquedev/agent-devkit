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

    def test_analyze_workload_architecture_filters_by_prefix(self) -> None:
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
                "analyze-workload-architecture",
                "--inventory",
                str(inventory),
                "--resource-prefix",
                "orders",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output_dir / "workload-components.json").exists())
            self.assertTrue((output_dir / "workload-architecture.md").exists())
            self.assertTrue((output_dir / "workload-open-questions.md").exists())
            components = json.loads((output_dir / "workload-components.json").read_text(encoding="utf-8"))

        self.assertGreater(len(components["resources"]), 0)
        names = [r["name"] for r in components["resources"]]
        self.assertTrue(any("orders" in n for n in names))

    def test_estimate_blast_radius_returns_direct_dependents(self) -> None:
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
                "estimate-blast-radius",
                "--resource-id",
                "arn:aws:iam::123456789012:role/orders-worker-role",
                "--inventory",
                str(inventory),
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output_dir / "blast-radius.json").exists())
            blast = json.loads((output_dir / "blast-radius.json").read_text(encoding="utf-8"))

        self.assertEqual(blast["resource_id"], "arn:aws:iam::123456789012:role/orders-worker-role")
        self.assertGreater(blast["direct_count"], 0)

    def test_review_resilience_emits_gap_when_has_dlq_missing(self) -> None:
        """SQS queue without has_dlq attribute should produce a gap finding, not medium."""
        with tempfile.TemporaryDirectory() as tmpdir:
            inventory = Path(tmpdir) / "inventory.json"
            output_dir = Path(tmpdir) / "out"
            # Use a fixture where SQS queue has NO has_dlq attribute at all
            payload = {
                "account_id": "123456789012",
                "region": "us-east-1",
                "resource_count": 1,
                "services": {"sqs": 1},
                "resources": [
                    {
                        "id": "arn:aws:sqs:us-east-1:123456789012:no-dlq-attr-queue",
                        "arn": "arn:aws:sqs:us-east-1:123456789012:no-dlq-attr-queue",
                        "name": "no-dlq-attr-queue",
                        "service": "sqs",
                        "resource_type": "queue",
                        "region": "us-east-1",
                        "account_id": "123456789012",
                        "relationships": [],
                        "attributes": {"queue_url": "https://sqs.us-east-1.amazonaws.com/123456789012/no-dlq-attr-queue"},
                    }
                ],
                "gaps": [],
            }
            inventory.write_text(json.dumps(payload), encoding="utf-8")

            result = self.run_cli(
                "run",
                "aws-architecture-analyst",
                "review-resilience",
                "--inventory",
                str(inventory),
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            findings_data = json.loads((output_dir / "resilience-findings.json").read_text(encoding="utf-8"))

        findings = findings_data["findings"]
        severities = [f["severity"] for f in findings]
        self.assertIn("gap", severities, "Expected a gap finding when has_dlq attribute is absent")

    def test_review_observability_detects_missing_alarms(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            inventory = Path(tmpdir) / "inventory.json"
            output_dir = Path(tmpdir) / "out"
            payload = {
                "account_id": "123456789012",
                "region": "us-east-1",
                "resource_count": 1,
                "services": {"lambda": 1},
                "resources": [
                    {
                        "id": "arn:aws:lambda:us-east-1:123456789012:function:test-fn",
                        "name": "test-fn",
                        "service": "lambda",
                        "resource_type": "function",
                        "region": "us-east-1",
                        "account_id": "123456789012",
                        "relationships": [],
                        "attributes": {},
                    }
                ],
                "gaps": [],
            }
            inventory.write_text(json.dumps(payload), encoding="utf-8")

            result = self.run_cli(
                "run",
                "aws-architecture-analyst",
                "review-observability",
                "--inventory",
                str(inventory),
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            findings_data = json.loads((output_dir / "observability-findings.json").read_text(encoding="utf-8"))

        findings = findings_data["findings"]
        self.assertTrue(any(f["severity"] == "medium" for f in findings), "Expected medium finding for no alarms")

    def test_review_networking_emits_gap_when_public_ip_missing(self) -> None:
        """EC2 instances without public_ip attribute should produce a gap finding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            inventory = Path(tmpdir) / "inventory.json"
            output_dir = Path(tmpdir) / "out"
            payload = {
                "account_id": "123456789012",
                "region": "us-east-1",
                "resource_count": 1,
                "services": {"ec2": 1},
                "resources": [
                    {
                        "id": "i-0123456789abcdef0",
                        "name": "prod-instance",
                        "service": "ec2",
                        "resource_type": "instance",
                        "region": "us-east-1",
                        "account_id": "123456789012",
                        "relationships": [],
                        "attributes": {"state": "running", "instance_type": "t3.micro"},
                    }
                ],
                "gaps": [],
            }
            inventory.write_text(json.dumps(payload), encoding="utf-8")

            result = self.run_cli(
                "run",
                "aws-architecture-analyst",
                "review-networking",
                "--inventory",
                str(inventory),
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            findings_data = json.loads((output_dir / "networking-findings.json").read_text(encoding="utf-8"))

        findings = findings_data["findings"]
        severities = [f["severity"] for f in findings]
        self.assertIn("gap", severities, "Expected a gap finding when public_ip attribute is absent from EC2 instance")


if __name__ == "__main__":
    unittest.main()
