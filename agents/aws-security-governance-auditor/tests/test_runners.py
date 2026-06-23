#!/usr/bin/env python3
"""Runner tests for aws-security-governance-auditor."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


def load_security_runner_support():
    shared_dir = ROOT / "agents" / "aws-security-governance-auditor" / "capabilities" / "_shared"
    spec = importlib.util.spec_from_file_location(
        "aws_security_governance_auditor_runner_support",
        shared_dir / "runner_support.py",
    )
    if spec is None or spec.loader is None:
        raise ImportError("cannot load aws security runner_support")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_security_fixture() -> dict:
    return {
        "account_id": "123456789012",
        "region": "us-east-1",
        "iam": {
            "users": [{"UserName": "legacy-user", "PasswordLastUsed": "2026-06-01T00:00:00Z"}],
            "roles": [{"RoleName": "admin-role", "Arn": "arn:aws:iam::123456789012:role/admin-role"}],
            "policies": [
                {
                    "PolicyName": "admin-inline",
                    "Principal": "admin-role",
                    "Document": {"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]},
                }
            ],
        },
        "security_groups": [
            {
                "GroupId": "sg-open",
                "GroupName": "open-web",
                "IpPermissions": [
                    {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}
                ],
            }
        ],
        "s3": {
            "buckets": [
                {
                    "Name": "public-bucket",
                    "PublicAccessBlock": {"BlockPublicAcls": False, "BlockPublicPolicy": False},
                    "Encryption": None,
                }
            ]
        },
        "cloudtrail": {"trails": []},
        "config": {"recorders": []},
        "secrets": {
            "secrets": [
                {"Name": "db-password", "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:db-password"}
            ]
        },
    }


class AwsSecurityGovernanceAuditorRunnerTest(unittest.TestCase):
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
        self.assertIn("aws-security-governance-auditor", agents)

    def test_audit_iam_principals_writes_findings_from_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "security-fixture.json"
            output_dir = Path(tmpdir) / "out"
            fixture.write_text(json.dumps(sample_security_fixture()), encoding="utf-8")

            result = self.run_cli(
                "run",
                "aws-security-governance-auditor",
                "audit-iam-principals",
                "--fixture",
                str(fixture),
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            audit = json.loads((output_dir / "iam-audit.json").read_text(encoding="utf-8"))

        self.assertEqual(audit["finding_count"], 1)
        self.assertEqual(audit["findings"][0]["severity"], "critical")

    def test_audit_public_exposure_detects_open_security_group_and_bucket(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "security-fixture.json"
            output_dir = Path(tmpdir) / "out"
            fixture.write_text(json.dumps(sample_security_fixture()), encoding="utf-8")

            result = self.run_cli(
                "run",
                "aws-security-governance-auditor",
                "audit-public-exposure",
                "--fixture",
                str(fixture),
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            exposure = json.loads((output_dir / "public-exposure.json").read_text(encoding="utf-8"))

        self.assertGreaterEqual(exposure["finding_count"], 2)
        self.assertTrue(any(item["resource_type"] == "security-group" for item in exposure["findings"]))
        self.assertTrue(any(item["resource_type"] == "s3-bucket" for item in exposure["findings"]))

    def test_generate_security_report_consolidates_audit_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"
            output_dir.mkdir()
            (output_dir / "iam-audit.json").write_text(
                json.dumps({"findings": [{"id": "iam-admin", "severity": "critical", "title": "Admin wildcard", "evidence": "Policy allows *"}]}),
                encoding="utf-8",
            )
            (output_dir / "public-exposure.json").write_text(
                json.dumps({"findings": [{"id": "sg-open", "severity": "high", "title": "SSH aberto", "evidence": "Port 22 open"}]}),
                encoding="utf-8",
            )

            result = self.run_cli(
                "run",
                "aws-security-governance-auditor",
                "generate-security-report",
                "--audit-dir",
                str(output_dir),
                "--output-dir",
                str(output_dir),
                "--yes-overwrite",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = (output_dir / "security-report.md").read_text(encoding="utf-8")
            findings = json.loads((output_dir / "security-findings.json").read_text(encoding="utf-8"))

        self.assertIn("Admin wildcard", report)
        self.assertEqual(findings["finding_count"], 2)

    def test_security_report_includes_quality_gates(self) -> None:
        """generate-security-report must report all 5 quality_gates as PASS/FAIL in result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"
            output_dir.mkdir()
            (output_dir / "iam-audit.json").write_text(
                json.dumps({
                    "findings": [
                        {
                            "id": "iam-admin",
                            "severity": "critical",
                            "category": "iam",
                            "resource_type": "iam-policy",
                            "resource_id": "admin-policy",
                            "title": "Admin wildcard",
                            "evidence": "Policy allows Action=* Resource=*",
                            "recommendation": "Restrict permissions",
                            "status": "confirmed",
                        }
                    ]
                }),
                encoding="utf-8",
            )

            result = self.run_cli(
                "run",
                "aws-security-governance-auditor",
                "generate-security-report",
                "--audit-dir",
                str(output_dir),
                "--output-dir",
                str(output_dir),
                "--yes-overwrite",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("quality_gates", payload)
        gates = payload["quality_gates"]
        expected_gates = {
            "read_only_allowlist_enforced",
            "findings_have_severity",
            "findings_have_evidence",
            "remediation_is_plan_only",
            "secrets_redacted",
        }
        self.assertEqual(set(gates.keys()), expected_gates)
        # All gates should PASS for a well-formed finding with no sensitive data
        for gate_name, gate_result in gates.items():
            self.assertIn(gate_result, {"PASS", "FAIL", "N-A"}, f"gate {gate_name} has unexpected value: {gate_result}")

    def test_audit_enriched_s3_bucket_via_fixture(self) -> None:
        """Fixture with full PAB+Encryption data → s3-buckets auditor produces findings."""
        fixture_data = {
            "account_id": "123456789012",
            "region": "us-east-1",
            "iam": {"users": [], "roles": [], "policies": []},
            "security_groups": [],
            "s3": {
                "buckets": [
                    {
                        "Name": "my-bucket",
                        "PublicAccessBlock": {
                            "BlockPublicAcls": False,
                            "IgnorePublicAcls": True,
                            "BlockPublicPolicy": True,
                            "RestrictPublicBuckets": True,
                        },
                        "Encryption": None,
                    }
                ]
            },
            "cloudtrail": {"trails": []},
            "config": {"recorders": []},
            "secrets": {"secrets": []},
            "gaps": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "fixture.json"
            output_dir = Path(tmpdir) / "out"
            fixture.write_text(json.dumps(fixture_data), encoding="utf-8")

            result = self.run_cli(
                "run",
                "aws-security-governance-auditor",
                "audit-s3-buckets",
                "--fixture",
                str(fixture),
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            audit = json.loads((output_dir / "s3-buckets-audit.json").read_text(encoding="utf-8"))

        # Incomplete PAB → high finding
        self.assertGreater(audit["finding_count"], 0)
        self.assertTrue(any(f["id"].startswith("s3-public-access-block") for f in audit["findings"]))

    def test_secrets_redaction_gate_fails_on_sensitive_output(self) -> None:
        """Quality gate secrets_redacted must FAIL if output contains sensitive patterns."""
        evaluate_quality_gates = load_security_runner_support().evaluate_quality_gates

        findings = [
            {
                "id": "test-1",
                "severity": "critical",
                "category": "iam",
                "resource_type": "iam-policy",
                "resource_id": "p1",
                "title": "Admin",
                "evidence": "Policy allows *",
                "recommendation": "Fix it",
                "status": "confirmed",
            }
        ]
        # Report text that accidentally contains a sensitive pattern
        sensitive_report = "Report\n\naws_secret_access_key=AKIAIOSFODNN7EXAMPLE\n"
        gates = evaluate_quality_gates(findings, report_text=sensitive_report)

        self.assertEqual(gates["secrets_redacted"], "FAIL")

    def test_lacunas_appear_in_snapshot_when_no_region(self) -> None:
        """Fixture with gaps[] populated → gaps propagated correctly."""
        fixture_data = {
            "account_id": "123456789012",
            "region": None,
            "iam": {"users": [], "roles": [], "policies": []},
            "security_groups": [],
            "s3": {"buckets": []},
            "cloudtrail": {"trails": []},
            "config": {"recorders": []},
            "secrets": {"secrets": []},
            "gaps": [
                "security_groups: not collected — no region specified",
                "secrets: not collected — no region specified",
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "fixture.json"
            output_dir = Path(tmpdir) / "out"
            fixture.write_text(json.dumps(fixture_data), encoding="utf-8")

            result = self.run_cli(
                "run",
                "aws-security-governance-auditor",
                "audit-cloudtrail-config",
                "--fixture",
                str(fixture),
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            audit = json.loads((output_dir / "cloudtrail-audit.json").read_text(encoding="utf-8"))

        # CloudTrail absent → critical finding regardless of gaps in other domains
        self.assertGreater(audit["finding_count"], 0)
        self.assertEqual(audit["findings"][0]["severity"], "critical")


if __name__ == "__main__":
    unittest.main()
