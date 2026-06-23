#!/usr/bin/env python3
"""Read-only AWS security governance repository backed by AWS CLI."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class AwsSecurityRepositoryError(RuntimeError):
    """Raised when AWS security repository cannot complete a read operation."""


ALLOWED_COMMANDS = {
    ("sts", "get-caller-identity"),
    ("iam", "list-users"),
    ("iam", "list-roles"),
    ("iam", "list-policies"),
    ("iam", "get-policy"),
    ("iam", "get-policy-version"),
    ("ec2", "describe-security-groups"),
    ("s3api", "list-buckets"),
    ("s3api", "get-public-access-block"),
    ("s3api", "get-bucket-encryption"),
    ("secretsmanager", "list-secrets"),
    ("cloudtrail", "describe-trails"),
    ("cloudtrail", "get-trail-status"),
    ("configservice", "describe-configuration-recorders"),
    ("configservice", "describe-config-rules"),
    ("kms", "list-keys"),
    ("kms", "describe-key"),
}


@dataclass(frozen=True)
class AwsSecurityConfig:
    default_region: str | None = None
    profile: str | None = None
    timeout_seconds: int = 60

    @classmethod
    def from_env(cls) -> "AwsSecurityConfig":
        load_dotenv()
        return cls(
            default_region=os.environ.get("AWS_REGION") or None,
            profile=os.environ.get("AWS_PROFILE") or None,
            timeout_seconds=int(os.environ.get("AWS_SECURITY_TIMEOUT", "60")),
        )


class AwsSecurityRepository:
    """Small read-only repository for AWS security metadata."""

    def __init__(self, config: AwsSecurityConfig | None = None) -> None:
        self.config = config or AwsSecurityConfig.from_env()

    def build_aws_command(self, args: list[str], *, region: str | None) -> list[str]:
        self._validate_allowed(args)
        command = ["aws", *args]
        resolved_region = region or self.config.default_region
        if resolved_region and "--region" not in command and args[0] not in {"iam", "sts", "s3api"}:
            command.extend(["--region", resolved_region])
        command.extend(["--output", "json"])
        if self.config.profile:
            command.extend(["--profile", self.config.profile])
        return command

    def aws_json(self, args: list[str], *, region: str | None = None) -> dict[str, Any]:
        command = self.build_aws_command(args, region=region)
        result = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self.config.timeout_seconds,
        )
        if result.returncode != 0:
            raise AwsSecurityRepositoryError(result.stderr.strip() or "aws cli failed")
        try:
            return json.loads(result.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise AwsSecurityRepositoryError(f"invalid aws cli json: {exc}") from exc

    def collect_security_snapshot(self, *, region: str | None = None) -> dict[str, Any]:
        resolved_region = region or self.config.default_region
        identity = self.aws_json(["sts", "get-caller-identity"], region=None)
        snapshot: dict[str, Any] = {
            "account_id": identity.get("Account"),
            "region": resolved_region,
            "iam": {
                "users": self.aws_json(["iam", "list-users"], region=None).get("Users", []),
                "roles": self.aws_json(["iam", "list-roles"], region=None).get("Roles", []),
                "policies": [],
            },
            "security_groups": [],
            "s3": {"buckets": []},
            "secrets": {"secrets": []},
            "cloudtrail": {"trails": []},
            "config": {"recorders": [], "rules": []},
            "gaps": [],
        }
        # Collect IAM customer-managed policies with their documents
        try:
            local_policies = self.aws_json(["iam", "list-policies", "--scope", "Local"], region=None).get("Policies", [])
            enriched_policies: list[dict[str, Any]] = []
            for policy in local_policies:
                policy_arn = policy.get("Arn")
                version_id = policy.get("DefaultVersionId")
                doc: dict[str, Any] = {}
                if policy_arn and version_id:
                    try:
                        doc = self.aws_json(
                            ["iam", "get-policy-version", "--policy-arn", policy_arn, "--version-id", version_id],
                            region=None,
                        ).get("PolicyVersion", {}).get("Document", {})
                    except AwsSecurityRepositoryError:
                        snapshot["gaps"].append(
                            f"iam: could not fetch policy document for {policy_arn}"
                        )
                enriched_policies.append({**policy, "Document": doc})
            snapshot["iam"]["policies"] = enriched_policies
        except AwsSecurityRepositoryError as exc:
            snapshot["gaps"].append(f"iam.policies: not collected — {exc}")
        if resolved_region:
            snapshot["security_groups"] = self.aws_json(["ec2", "describe-security-groups"], region=resolved_region).get("SecurityGroups", [])
            snapshot["secrets"]["secrets"] = self.aws_json(["secretsmanager", "list-secrets"], region=resolved_region).get("SecretList", [])
            snapshot["cloudtrail"]["trails"] = self.aws_json(["cloudtrail", "describe-trails"], region=resolved_region).get("trailList", [])
            snapshot["config"]["recorders"] = self.aws_json(["configservice", "describe-configuration-recorders"], region=resolved_region).get("ConfigurationRecorders", [])
            snapshot["config"]["rules"] = self.aws_json(["configservice", "describe-config-rules"], region=resolved_region).get("ConfigRules", [])
        else:
            snapshot["gaps"].append("security_groups: not collected — no region specified")
            snapshot["gaps"].append("secrets: not collected — no region specified")
            snapshot["gaps"].append("cloudtrail: not collected — no region specified")
            snapshot["gaps"].append("config: not collected — no region specified")
        # Collect S3 buckets with PAB and Encryption per bucket
        raw_buckets = self.aws_json(["s3api", "list-buckets"], region=None).get("Buckets", [])
        enriched_buckets: list[dict[str, Any]] = []
        for item in raw_buckets:
            name = item.get("Name") or ""
            bucket: dict[str, Any] = {"Name": name}
            try:
                pab_data = self.aws_json(
                    ["s3api", "get-public-access-block", "--bucket", name], region=None
                ).get("PublicAccessBlockConfiguration", {})
                bucket["PublicAccessBlock"] = pab_data
            except AwsSecurityRepositoryError:
                snapshot["gaps"].append(f"s3.{name}.PublicAccessBlock: not collected")
            try:
                enc_data = self.aws_json(
                    ["s3api", "get-bucket-encryption", "--bucket", name], region=None
                ).get("ServerSideEncryptionConfiguration", {})
                bucket["Encryption"] = enc_data
            except AwsSecurityRepositoryError:
                snapshot["gaps"].append(f"s3.{name}.Encryption: not collected")
            enriched_buckets.append(bucket)
        snapshot["s3"]["buckets"] = enriched_buckets
        return snapshot

    def _validate_allowed(self, args: list[str]) -> None:
        if len(args) < 2 or (args[0], args[1]) not in ALLOWED_COMMANDS:
            raise AwsSecurityRepositoryError(f"aws command is not allowed: {' '.join(args[:2])}")


def load_dotenv() -> None:
    for candidate in dotenv_candidates():
        if not candidate.exists():
            continue
        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def dotenv_candidates() -> list[Path]:
    paths = [Path.cwd() / ".env", Path.cwd() / ".env.local"]
    paths.extend(parent / ".env" for parent in Path(__file__).resolve().parents)
    unique = []
    seen = set()
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique
