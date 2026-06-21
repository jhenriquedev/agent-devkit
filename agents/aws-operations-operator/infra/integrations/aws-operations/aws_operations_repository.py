#!/usr/bin/env python3
"""AWS operations repository with dry-run and confirmation guardrails."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any


class AwsOperationsRepositoryError(RuntimeError):
    """Raised when an AWS operation violates guardrails or fails."""


ALLOWED_MUTATIONS = {
    ("ecs", "update-service"),
    ("lambda", "invoke"),
    ("cloudfront", "create-invalidation"),
    ("autoscaling", "set-desired-capacity"),
    ("events", "enable-rule"),
    ("events", "disable-rule"),
}

BLOCKED_DESTRUCTIVE = {
    ("sqs", "purge-queue"),
    ("sqs", "start-message-move-task"),
}


@dataclass(frozen=True)
class AwsOperationsConfig:
    default_region: str | None = None
    profile: str | None = None
    timeout_seconds: int = 60
    allowed_accounts: dict[str, set[str]] | None = None
    environment_regions: dict[str, str] | None = None

    @classmethod
    def from_env(cls) -> "AwsOperationsConfig":
        load_dotenv()
        return cls(
            default_region=os.environ.get("AWS_REGION") or None,
            profile=os.environ.get("AWS_PROFILE") or None,
            timeout_seconds=int(os.environ.get("AWS_OPERATIONS_TIMEOUT", "60")),
            allowed_accounts=parse_allowed_accounts(os.environ),
            environment_regions=parse_environment_regions(os.environ),
        )


@dataclass(frozen=True)
class AwsOperation:
    operation: str
    resource_id: str
    args: list[str]
    destructive: bool = False
    rollback_hint: str = "Reverter manualmente conforme estado anterior validado antes da operacao."
    display_args: list[str] | None = None

    @staticmethod
    def force_ecs_deployment(*, cluster: str, service: str) -> "AwsOperation":
        return AwsOperation(
            operation="force-ecs-deployment",
            resource_id=f"{cluster}/{service}",
            args=[
                "ecs",
                "update-service",
                "--cluster",
                cluster,
                "--service",
                service,
                "--force-new-deployment",
            ],
            rollback_hint="Nao ha rollback direto; validar task definition anterior e executar novo deployment se necessario.",
        )

    @staticmethod
    def restart_ecs_service(*, cluster: str, service: str) -> "AwsOperation":
        operation = AwsOperation.force_ecs_deployment(cluster=cluster, service=service)
        return AwsOperation(
            operation="restart-ecs-service",
            resource_id=operation.resource_id,
            args=operation.args,
            rollback_hint="Restart via novo deployment; validar tasks antigas e novas ate o service estabilizar.",
        )

    @staticmethod
    def invoke_lambda(*, function_name: str, payload: str | None = None) -> "AwsOperation":
        args = ["lambda", "invoke", "--function-name", function_name, "--cli-binary-format", "raw-in-base64-out"]
        display_args = list(args)
        if payload:
            args.extend(["--payload", payload])
            display_args.extend(["--payload", redacted_payload_marker(payload)])
        args.append("{lambda_output_file}")
        display_args.append("<lambda-output-file>")
        return AwsOperation(
            operation="invoke-lambda",
            resource_id=function_name,
            args=args,
            display_args=display_args,
            rollback_hint="Lambda invoke nao possui rollback automatico; validar efeitos colaterais do handler.",
        )

    @staticmethod
    def invalidate_cloudfront(*, distribution_id: str, paths: str) -> "AwsOperation":
        return AwsOperation(
            operation="invalidate-cloudfront-cache",
            resource_id=distribution_id,
            args=[
                "cloudfront",
                "create-invalidation",
                "--distribution-id",
                distribution_id,
                "--paths",
                *paths.split(),
            ],
            rollback_hint="Invalidation nao pode ser desfeita; aguardar propagacao e validar cache.",
        )

    @staticmethod
    def scale_autoscaling_group(*, auto_scaling_group: str, desired_capacity: int) -> "AwsOperation":
        return AwsOperation(
            operation="scale-autoscaling-group",
            resource_id=auto_scaling_group,
            args=[
                "autoscaling",
                "set-desired-capacity",
                "--auto-scaling-group-name",
                auto_scaling_group,
                "--desired-capacity",
                str(desired_capacity),
                "--honor-cooldown",
            ],
            rollback_hint="Restaurar desired capacity anterior apos validacao.",
        )

    @staticmethod
    def toggle_eventbridge_rule(*, rule_name: str, action: str) -> "AwsOperation":
        if action not in {"enable", "disable"}:
            raise AwsOperationsRepositoryError("action must be enable or disable")
        return AwsOperation(
            operation="toggle-eventbridge-rule",
            resource_id=rule_name,
            args=["events", f"{action}-rule", "--name", rule_name],
            rollback_hint=f"Executar action oposta para reverter: {'disable' if action == 'enable' else 'enable'}.",
        )

    @staticmethod
    def purge_sqs_plan(*, queue_url: str) -> "AwsOperation":
        return AwsOperation(
            operation="purge-sqs-queue-plan",
            resource_id=queue_url,
            args=["sqs", "purge-queue", "--queue-url", queue_url],
            destructive=True,
            rollback_hint="Purge de SQS nao tem rollback. Validar backup/reprocessamento antes de qualquer execucao manual.",
        )

    @staticmethod
    def redrive_sqs_plan(*, source_arn: str, destination_arn: str) -> "AwsOperation":
        return AwsOperation(
            operation="redrive-sqs-dlq",
            resource_id=source_arn,
            args=[
                "sqs",
                "start-message-move-task",
                "--source-arn",
                source_arn,
                "--destination-arn",
                destination_arn,
            ],
            destructive=True,
            rollback_hint="Redrive pode duplicar processamento. Validar idempotencia antes de execucao manual.",
        )


class AwsOperationsRepository:
    """AWS operations wrapper enforcing dry-run and confirmation."""

    def __init__(self, config: AwsOperationsConfig | None = None) -> None:
        self.config = config or AwsOperationsConfig.from_env()

    def build_aws_command(
        self,
        operation: AwsOperation,
        *,
        region: str | None = None,
        include_sensitive: bool = False,
        lambda_output_path: str | None = None,
    ) -> list[str]:
        self._validate_allowed(operation)
        operation_args = operation.args if include_sensitive else operation.display_args or operation.args
        command = ["aws", *replace_lambda_output_file(operation_args, lambda_output_path, include_sensitive)]
        resolved_region = region or self.config.default_region
        if resolved_region and "--region" not in command and operation.args[0] not in {"cloudfront"}:
            command.extend(["--region", resolved_region])
        command.extend(["--output", "json"])
        if self.config.profile:
            command.extend(["--profile", self.config.profile])
        return command

    def run_operation(
        self,
        operation: AwsOperation,
        *,
        environment: str,
        execute: bool,
        confirm_resource: str | None,
        region: str | None = None,
    ) -> dict[str, Any]:
        resolved_environment = normalize_environment(environment)
        resolved_region = self.resolve_region(resolved_environment, region)
        display_command = self.build_aws_command(operation, region=resolved_region)
        base = {
            "operation": operation.operation,
            "resource_id": operation.resource_id,
            "environment": resolved_environment,
            "region": resolved_region,
            "profile": self.config.profile,
            "execute": execute,
            "aws_command": display_command,
            "display_command": display_command,
            "destructive": operation.destructive,
            "rollback_hint": operation.rollback_hint,
        }
        if operation.destructive:
            if execute:
                raise AwsOperationsRepositoryError("destructive operations are blocked by default")
            return {**base, "status": "blocked-plan-only"}
        if not execute:
            return {**base, "status": "planned"}
        self._validate_execute(operation, environment=resolved_environment, confirm_resource=confirm_resource)
        account_validation = self.validate_account(resolved_environment, resolved_region)
        preflight = self.collect_preflight(operation, resolved_region)
        lambda_output_path = None
        if operation.operation == "invoke-lambda":
            lambda_output_path = str(Path(tempfile.mkdtemp(prefix="aws-operations-")) / "lambda-output.json")
        command = self.build_aws_command(
            operation,
            region=resolved_region,
            include_sensitive=True,
            lambda_output_path=lambda_output_path,
        )
        result = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self.config.timeout_seconds,
        )
        if result.returncode != 0:
            raise AwsOperationsRepositoryError(result.stderr.strip() or "aws cli failed")
        lambda_response = read_lambda_response(lambda_output_path)
        post_check = self.collect_post_check(operation, resolved_region, result.stdout, lambda_response)
        return {
            **base,
            "status": "executed",
            "account_validation": account_validation,
            "preflight": preflight,
            "post_check": post_check,
            "returncode": result.returncode,
            "stdout": safe_json_or_text(result.stdout),
            "lambda_response": lambda_response,
        }

    def _validate_execute(self, operation: AwsOperation, *, environment: str, confirm_resource: str | None) -> None:
        if not confirm_resource:
            raise AwsOperationsRepositoryError("execute requires --confirm-resource")
        if confirm_resource != operation.resource_id:
            raise AwsOperationsRepositoryError("confirm resource does not match operation resource")
        if not environment:
            raise AwsOperationsRepositoryError("environment is required")
        if environment.lower() in {"prod", "production"}:
            raise AwsOperationsRepositoryError("production execution requires --environment prd exactly")

    def resolve_region(self, environment: str, explicit_region: str | None) -> str | None:
        if explicit_region:
            return explicit_region
        environment_regions = self.config.environment_regions or {}
        return environment_regions.get(environment) or self.config.default_region

    def validate_account(self, environment: str, region: str | None) -> dict[str, Any]:
        allowed_accounts = self.config.allowed_accounts or {}
        expected_accounts = allowed_accounts.get(environment)
        if not expected_accounts:
            raise AwsOperationsRepositoryError(
                f"no allowed AWS accounts configured for environment: {environment}"
            )
        identity = self.run_json_command(["sts", "get-caller-identity"], region=region, include_region=False)
        account_id = str(identity.get("Account") or "")
        if account_id not in expected_accounts:
            raise AwsOperationsRepositoryError(
                f"AWS account {account_id or '-'} is not allowed for environment {environment}"
            )
        return {
            "environment": environment,
            "account_id": account_id,
            "arn": identity.get("Arn"),
            "user_id": identity.get("UserId"),
            "allowed_accounts": sorted(expected_accounts),
        }

    def collect_preflight(self, operation: AwsOperation, region: str | None) -> dict[str, Any]:
        command = self.preflight_command(operation)
        if not command:
            return {"kind": operation.operation, "status": "not-supported"}
        return {
            "kind": preflight_kind(operation),
            "resource_id": operation.resource_id,
            "state": self.run_json_command(command, region=region, include_region=command[0] != "cloudfront"),
        }

    def collect_post_check(
        self,
        operation: AwsOperation,
        region: str | None,
        stdout: str,
        lambda_response: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if operation.operation == "invoke-lambda":
            invoke_result = safe_json_or_text(stdout)
            return {
                "kind": "lambda",
                "resource_id": operation.resource_id,
                "status_code": invoke_result.get("StatusCode") if isinstance(invoke_result, dict) else None,
                "function_error": invoke_result.get("FunctionError") if isinstance(invoke_result, dict) else None,
                "executed_version": invoke_result.get("ExecutedVersion") if isinstance(invoke_result, dict) else None,
                "response_payload_hash": (lambda_response or {}).get("payload_hash"),
            }
        return self.collect_preflight(operation, region)

    def preflight_command(self, operation: AwsOperation) -> list[str] | None:
        if operation.args[:2] == ["ecs", "update-service"]:
            return [
                "ecs",
                "describe-services",
                "--cluster",
                value_after(operation.args, "--cluster"),
                "--services",
                value_after(operation.args, "--service"),
            ]
        if operation.args[:2] == ["lambda", "invoke"]:
            return [
                "lambda",
                "get-function-configuration",
                "--function-name",
                value_after(operation.args, "--function-name"),
            ]
        if operation.args[:2] == ["cloudfront", "create-invalidation"]:
            return [
                "cloudfront",
                "get-distribution",
                "--id",
                value_after(operation.args, "--distribution-id"),
            ]
        if operation.args[:2] == ["autoscaling", "set-desired-capacity"]:
            return [
                "autoscaling",
                "describe-auto-scaling-groups",
                "--auto-scaling-group-names",
                value_after(operation.args, "--auto-scaling-group-name"),
            ]
        if operation.args[0] == "events" and operation.args[1] in {"enable-rule", "disable-rule"}:
            return ["events", "describe-rule", "--name", value_after(operation.args, "--name")]
        return None

    def run_json_command(self, args: list[str], *, region: str | None, include_region: bool = True) -> dict[str, Any]:
        command = ["aws", *args]
        if region and include_region and "--region" not in command:
            command.extend(["--region", region])
        command.extend(["--output", "json"])
        if self.config.profile:
            command.extend(["--profile", self.config.profile])
        result = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self.config.timeout_seconds,
        )
        if result.returncode != 0:
            raise AwsOperationsRepositoryError(result.stderr.strip() or f"aws cli failed: {' '.join(args[:2])}")
        parsed = safe_json_or_text(result.stdout)
        return parsed if isinstance(parsed, dict) else {"text": parsed}

    def _validate_allowed(self, operation: AwsOperation) -> None:
        if len(operation.args) < 2:
            raise AwsOperationsRepositoryError("operation command is incomplete")
        pair = (operation.args[0], operation.args[1])
        if operation.destructive and pair in BLOCKED_DESTRUCTIVE:
            return
        if pair not in ALLOWED_MUTATIONS:
            raise AwsOperationsRepositoryError(f"aws operation is not allowed: {' '.join(pair)}")


def safe_json_or_text(value: str) -> Any:
    try:
        return json.loads(value or "{}")
    except json.JSONDecodeError:
        return value[:2000]


def read_lambda_response(output_path: str | None) -> dict[str, Any] | None:
    if not output_path:
        return None
    path = Path(output_path)
    if not path.exists():
        return {"payload_hash": None, "payload_bytes": 0, "payload_present": False}
    raw = path.read_bytes()
    try:
        path.unlink()
        path.parent.rmdir()
    except OSError:
        pass
    return {
        "payload_hash": sha256(raw).hexdigest(),
        "payload_bytes": len(raw),
        "payload_present": True,
    }


def redacted_payload_marker(payload: str) -> str:
    raw = payload.encode("utf-8")
    return f"<redacted sha256={sha256(raw).hexdigest()} bytes={len(raw)}>"


def replace_lambda_output_file(args: list[str], output_path: str | None, include_sensitive: bool) -> list[str]:
    replacement = output_path if include_sensitive and output_path else "<lambda-output-file>"
    return [replacement if part == "{lambda_output_file}" else part for part in args]


def value_after(args: list[str], flag: str) -> str:
    try:
        return args[args.index(flag) + 1]
    except (ValueError, IndexError) as exc:
        raise AwsOperationsRepositoryError(f"missing required operation argument: {flag}") from exc


def normalize_environment(environment: str) -> str:
    return environment.strip().lower()


def preflight_kind(operation: AwsOperation) -> str:
    if operation.args:
        return operation.args[0]
    return operation.operation


def parse_allowed_accounts(environ: os._Environ[str]) -> dict[str, set[str]]:
    prefix = "AWS_OPERATIONS_ALLOWED_ACCOUNTS_"
    allowed: dict[str, set[str]] = {}
    for key, value in environ.items():
        if not key.startswith(prefix):
            continue
        environment = key[len(prefix) :].lower()
        accounts = {item.strip() for item in value.replace(";", ",").split(",") if item.strip()}
        if accounts:
            allowed[environment] = accounts
    return allowed


def parse_environment_regions(environ: os._Environ[str]) -> dict[str, str]:
    prefix = "AWS_OPERATIONS_DEFAULT_REGION_"
    regions: dict[str, str] = {}
    for key, value in environ.items():
        if key.startswith(prefix) and value.strip():
            regions[key[len(prefix) :].lower()] = value.strip()
    return regions


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
