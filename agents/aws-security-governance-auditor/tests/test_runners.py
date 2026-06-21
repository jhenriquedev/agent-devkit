#!/usr/bin/env python3
"""Runner tests for aws-security-governance-auditor."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


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
                json.dumps({"findings": [{"id": "iam-admin", "severity": "critical", "title": "Admin wildcard"}]}),
                encoding="utf-8",
            )
            (output_dir / "public-exposure.json").write_text(
                json.dumps({"findings": [{"id": "sg-open", "severity": "high", "title": "SSH aberto"}]}),
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


if __name__ == "__main__":
    unittest.main()
