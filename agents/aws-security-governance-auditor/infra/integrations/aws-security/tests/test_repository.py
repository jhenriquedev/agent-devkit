#!/usr/bin/env python3
"""Tests for AWS security governance repository."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


AWS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AWS_DIR))

from auditors import audit_iam_principals, audit_public_exposure  # noqa: E402
from aws_security_repository import AwsSecurityConfig, AwsSecurityRepository, AwsSecurityRepositoryError  # noqa: E402


class AwsSecurityRepositoryTest(unittest.TestCase):
    def test_blocks_commands_outside_allowlist(self) -> None:
        repo = AwsSecurityRepository(AwsSecurityConfig(default_region="us-east-1"))

        with self.assertRaises(AwsSecurityRepositoryError):
            repo.aws_json(["iam", "delete-user", "--user-name", "legacy"], region=None)

    def test_builds_command_with_profile_and_region(self) -> None:
        repo = AwsSecurityRepository(AwsSecurityConfig(default_region="us-east-1", profile="dev"))

        command = repo.build_aws_command(["ec2", "describe-security-groups"], region=None)

        self.assertIn("--region", command)
        self.assertIn("us-east-1", command)
        self.assertEqual(command[-4:], ["--output", "json", "--profile", "dev"])

    def test_audits_iam_wildcard_admin_policy(self) -> None:
        findings = audit_iam_principals(
            {
                "iam": {
                    "policies": [
                        {
                            "PolicyName": "admin",
                            "Principal": "role-a",
                            "Document": {"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]},
                        }
                    ]
                }
            }
        )

        self.assertEqual(findings[0]["severity"], "critical")
        self.assertEqual(findings[0]["category"], "iam")

    def test_audits_public_exposure(self) -> None:
        findings = audit_public_exposure(
            {
                "security_groups": [
                    {
                        "GroupId": "sg-1",
                        "GroupName": "open",
                        "IpPermissions": [
                            {"FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}
                        ],
                    }
                ],
                "s3": {"buckets": [{"Name": "bucket", "PublicAccessBlock": {"BlockPublicPolicy": False}}]},
            }
        )

        self.assertEqual(len(findings), 2)
        self.assertTrue(any(item["resource_type"] == "security-group" for item in findings))


if __name__ == "__main__":
    unittest.main()
