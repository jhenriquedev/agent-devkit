#!/usr/bin/env python3
"""Read-only AWS architecture repository backed by AWS CLI."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from normalizers import normalize_generic_resource, normalize_lambda_function, service_counts


class AwsArchitectureRepositoryError(RuntimeError):
    """Raised when AWS architecture repository cannot complete a read operation."""


ALLOWED_COMMANDS = {
    ("sts", "get-caller-identity"),
    ("lambda", "list-functions"),
    ("ecs", "list-clusters"),
    ("ecs", "describe-clusters"),
    ("ecs", "list-services"),
    ("ecs", "describe-services"),
    ("ec2", "describe-instances"),
    ("ec2", "describe-vpcs"),
    ("ec2", "describe-subnets"),
    ("ec2", "describe-route-tables"),
    ("ec2", "describe-security-groups"),
    ("elbv2", "describe-load-balancers"),
    ("elbv2", "describe-target-groups"),
    ("apigateway", "get-rest-apis"),
    ("apigatewayv2", "get-apis"),
    ("s3api", "list-buckets"),
    ("s3api", "get-bucket-location"),
    ("rds", "describe-db-instances"),
    ("dynamodb", "list-tables"),
    ("dynamodb", "describe-table"),
    ("sqs", "list-queues"),
    ("sqs", "get-queue-attributes"),
    ("sns", "list-topics"),
    ("events", "list-rules"),
    ("cloudwatch", "describe-alarms"),
    ("logs", "describe-log-groups"),
}


@dataclass(frozen=True)
class AwsArchitectureConfig:
    default_region: str | None = None
    profile: str | None = None
    timeout_seconds: int = 60

    @classmethod
    def from_env(cls) -> "AwsArchitectureConfig":
        load_dotenv()
        return cls(
            default_region=os.environ.get("AWS_REGION") or None,
            profile=os.environ.get("AWS_PROFILE") or None,
            timeout_seconds=int(os.environ.get("AWS_ARCHITECTURE_TIMEOUT", "60")),
        )


class AwsArchitectureRepository:
    """Small read-only repository for architecture inventory."""

    def __init__(self, config: AwsArchitectureConfig | None = None) -> None:
        self.config = config or AwsArchitectureConfig.from_env()

    def build_aws_command(self, args: list[str], *, region: str | None) -> list[str]:
        self._validate_allowed(args)
        command = ["aws", *args]
        resolved_region = region or self.config.default_region
        if resolved_region and "--region" not in command and args[0] not in {"s3api", "sts"}:
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
            raise AwsArchitectureRepositoryError(result.stderr.strip() or "aws cli failed")
        try:
            return json.loads(result.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise AwsArchitectureRepositoryError(f"invalid aws cli json: {exc}") from exc

    def discover_account_inventory(
        self,
        *,
        region: str | None = None,
        account_id: str | None = None,
    ) -> dict[str, Any]:
        resolved_region = self._resolve_region(region)
        identity = self.aws_json(["sts", "get-caller-identity"], region=None)
        resolved_account = account_id or identity.get("Account")
        resources: list[dict[str, Any]] = []
        gaps: list[dict[str, str]] = []

        collectors = [
            ("lambda", lambda: self._collect_lambda(resolved_region, resolved_account)),
            ("ec2", lambda: self._collect_ec2_instances(resolved_region, resolved_account)),
            ("sqs", lambda: self._collect_sqs(resolved_region, resolved_account)),
            ("sns", lambda: self._collect_sns(resolved_region, resolved_account)),
            ("cloudwatch", lambda: self._collect_cloudwatch_alarms(resolved_region, resolved_account)),
            ("logs", lambda: self._collect_log_groups(resolved_region, resolved_account)),
        ]
        for service, collector in collectors:
            try:
                resources.extend(collector())
            except AwsArchitectureRepositoryError as exc:
                gaps.append({"service": service, "message": str(exc)})

        return build_inventory(
            account_id=resolved_account,
            region=resolved_region,
            resources=resources,
            gaps=gaps,
            profile=self.config.profile,
        )

    def _collect_lambda(self, region: str, account_id: str | None) -> list[dict[str, Any]]:
        payload = self.aws_json(["lambda", "list-functions"], region=region)
        return [
            normalize_lambda_function(item, account_id=account_id, region=region)
            for item in payload.get("Functions", [])
        ]

    def _collect_ec2_instances(self, region: str, account_id: str | None) -> list[dict[str, Any]]:
        payload = self.aws_json(["ec2", "describe-instances"], region=region)
        resources = []
        for reservation in payload.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instance_id = instance.get("InstanceId")
                resources.append(
                    normalize_generic_resource(
                        service="ec2",
                        resource_type="instance",
                        resource_id=instance_id,
                        arn=None,
                        name=tag_name(instance.get("Tags") or []) or instance_id,
                        region=region,
                        account_id=account_id,
                        attributes={"state": (instance.get("State") or {}).get("Name"), "instance_type": instance.get("InstanceType")},
                        source_method="ec2.describe-instances",
                    )
                )
        return resources

    def _collect_sqs(self, region: str, account_id: str | None) -> list[dict[str, Any]]:
        payload = self.aws_json(["sqs", "list-queues"], region=region)
        resources = []
        for url in payload.get("QueueUrls", []):
            name = str(url).rstrip("/").split("/")[-1]
            arn = f"arn:aws:sqs:{region}:{account_id}:{name}" if account_id else url
            resources.append(
                normalize_generic_resource(
                    service="sqs",
                    resource_type="queue",
                    resource_id=arn,
                    arn=arn,
                    name=name,
                    region=region,
                    account_id=account_id,
                    attributes={"queue_url": url},
                    source_method="sqs.list-queues",
                )
            )
        return resources

    def _collect_sns(self, region: str, account_id: str | None) -> list[dict[str, Any]]:
        payload = self.aws_json(["sns", "list-topics"], region=region)
        return [
            normalize_generic_resource(
                service="sns",
                resource_type="topic",
                resource_id=item.get("TopicArn"),
                arn=item.get("TopicArn"),
                name=str(item.get("TopicArn", "")).split(":")[-1],
                region=region,
                account_id=account_id,
                source_method="sns.list-topics",
            )
            for item in payload.get("Topics", [])
        ]

    def _collect_cloudwatch_alarms(self, region: str, account_id: str | None) -> list[dict[str, Any]]:
        payload = self.aws_json(["cloudwatch", "describe-alarms"], region=region)
        return [
            normalize_generic_resource(
                service="cloudwatch",
                resource_type="alarm",
                resource_id=item.get("AlarmArn") or item.get("AlarmName"),
                arn=item.get("AlarmArn"),
                name=item.get("AlarmName") or "unknown-alarm",
                region=region,
                account_id=account_id,
                attributes={"state": item.get("StateValue"), "namespace": item.get("Namespace")},
                source_method="cloudwatch.describe-alarms",
            )
            for item in payload.get("MetricAlarms", [])
        ]

    def _collect_log_groups(self, region: str, account_id: str | None) -> list[dict[str, Any]]:
        payload = self.aws_json(["logs", "describe-log-groups"], region=region)
        return [
            normalize_generic_resource(
                service="logs",
                resource_type="log-group",
                resource_id=item.get("arn") or item.get("logGroupName"),
                arn=item.get("arn"),
                name=item.get("logGroupName") or "unknown-log-group",
                region=region,
                account_id=account_id,
                attributes={"retention_in_days": item.get("retentionInDays"), "stored_bytes": item.get("storedBytes")},
                source_method="logs.describe-log-groups",
            )
            for item in payload.get("logGroups", [])
        ]

    def _resolve_region(self, region: str | None) -> str:
        resolved = region or self.config.default_region
        if not resolved:
            raise AwsArchitectureRepositoryError("region is required")
        return resolved

    def _validate_allowed(self, args: list[str]) -> None:
        if len(args) < 2 or (args[0], args[1]) not in ALLOWED_COMMANDS:
            raise AwsArchitectureRepositoryError(f"aws command is not allowed: {' '.join(args[:2])}")


def build_inventory(
    *,
    account_id: str | None,
    region: str,
    resources: list[dict[str, Any]],
    gaps: list[dict[str, str]] | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "account_id": account_id,
        "region": region,
        "profile": profile,
        "resource_count": len(resources),
        "services": service_counts(resources),
        "resources": resources,
        "gaps": gaps or [],
    }


def tag_name(tags: list[dict[str, Any]]) -> str | None:
    for tag in tags:
        if tag.get("Key") == "Name":
            return tag.get("Value")
    return None


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
    paths: list[Path] = []
    current = Path.cwd()
    if current.is_dir():
        paths.extend([current / ".env", current / ".env.local"])
    for parent in Path(__file__).resolve().parents:
        paths.append(parent / ".env")
    unique = []
    seen = set()
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique
