#!/usr/bin/env python3
"""Shared runner support for AWS Operations Operator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
AWS_DIR = AGENT_DIR / "infra" / "integrations" / "aws-operations"

sys.path.insert(0, str(AWS_DIR))

from aws_operations_repository import (  # pylint: disable=import-error
    AwsOperation,
    AwsOperationsConfig,
    AwsOperationsRepository,
)
from report_renderer import render_operation_plan, render_operation_report, render_rollback_notes  # pylint: disable=import-error


PLAN_OPERATION_POLICY = {
    "force-ecs-deployment": {"destructive": False, "status": "planned"},
    "restart-ecs-service": {"destructive": False, "status": "planned"},
    "invoke-lambda": {"destructive": False, "status": "planned"},
    "invalidate-cloudfront-cache": {"destructive": False, "status": "planned"},
    "scale-autoscaling-group": {"destructive": False, "status": "planned"},
    "toggle-eventbridge-rule": {"destructive": False, "status": "planned"},
    "redrive-sqs-dlq": {"destructive": True, "status": "blocked-plan-only"},
    "purge-sqs-queue-plan": {"destructive": True, "status": "blocked-plan-only"},
}


def add_common_operation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile")
    parser.add_argument("--region")
    parser.add_argument("--environment", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-resource")
    add_common_output_args(parser)


def add_common_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-dir")
    parser.add_argument("--yes-create-dir", action="store_true")
    parser.add_argument("--yes-overwrite", action="store_true")


def resolve_output_dir(output_dir: str | None, create: bool) -> Path:
    path = Path(output_dir or ".").expanduser().resolve()
    if not path.exists():
        if not create:
            raise ValueError(f"output directory does not exist; pass --yes-create-dir: {path}")
        path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise ValueError(f"output path is not a directory: {path}")
    return path


def write_json(path: Path, payload: Any, overwrite: bool) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", overwrite)


def write_text(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise ValueError(f"artifact already exists; pass --yes-overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def operation_repo(args: argparse.Namespace) -> AwsOperationsRepository:
    base = AwsOperationsConfig.from_env()
    return AwsOperationsRepository(
        AwsOperationsConfig(
            default_region=args.region or base.default_region,
            profile=args.profile or base.profile,
            timeout_seconds=base.timeout_seconds,
            allowed_accounts=base.allowed_accounts,
            environment_regions=base.environment_regions,
        )
    )


def persist_operation(output_dir: Path, payload: dict[str, Any], overwrite: bool) -> None:
    write_json(output_dir / "operation-dry-run.json", payload, overwrite)
    write_text(output_dir / "operation-plan.md", render_operation_plan(payload), overwrite)
    write_text(output_dir / "rollback-notes.md", render_rollback_notes(payload), overwrite)
    if payload.get("account_validation"):
        write_json(output_dir / "account-validation.json", payload["account_validation"], overwrite)
    if payload.get("preflight"):
        write_json(output_dir / "preflight.json", payload["preflight"], overwrite)
    if payload.get("post_check"):
        write_json(output_dir / "post-check.json", payload["post_check"], overwrite)
    if payload.get("status") == "executed":
        write_json(output_dir / "operation-result.json", payload, overwrite)


def run_operation(operation: AwsOperation, args: argparse.Namespace) -> int:
    try:
        output_dir = resolve_output_dir(args.output_dir, args.yes_create_dir)
        payload = operation_repo(args).run_operation(
            operation,
            environment=args.environment,
            execute=args.execute,
            confirm_resource=args.confirm_resource,
            region=args.region,
        )
        persist_operation(output_dir, payload, args.yes_overwrite)
        print(json.dumps({"output_dir": str(output_dir), "status": payload.get("status"), "execute": payload.get("execute")}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


def run_plan_action() -> int:
    parser = argparse.ArgumentParser(description="Plan AWS operational action")
    parser.add_argument("--operation", required=True)
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--environment", required=True)
    add_common_output_args(parser)
    args = parser.parse_args()
    policy = PLAN_OPERATION_POLICY.get(args.operation)
    if not policy:
        print(json.dumps({"error": f"operation is not allowed for planning: {args.operation}"}, ensure_ascii=False), file=sys.stderr)
        return 1
    operation = AwsOperation(
        operation=args.operation,
        resource_id=args.resource_id,
        args=["manual", "plan", "--resource-id", args.resource_id],
    )
    payload = {
        "operation": operation.operation,
        "resource_id": operation.resource_id,
        "environment": args.environment,
        "execute": False,
        "aws_command": operation.args,
        "display_command": operation.args,
        "destructive": policy["destructive"],
        "rollback_hint": "Definir rollback especifico antes de executar.",
        "status": policy["status"],
    }
    try:
        output_dir = resolve_output_dir(args.output_dir, args.yes_create_dir)
        persist_operation(output_dir, payload, args.yes_overwrite)
        print(json.dumps({"output_dir": str(output_dir), "status": "planned"}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


def run_force_ecs_deployment() -> int:
    parser = argparse.ArgumentParser(description="Force ECS deployment")
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--service", required=True)
    add_common_operation_args(parser)
    args = parser.parse_args()
    return run_operation(AwsOperation.force_ecs_deployment(cluster=args.cluster, service=args.service), args)


def run_restart_ecs_service() -> int:
    parser = argparse.ArgumentParser(description="Restart ECS service")
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--service", required=True)
    add_common_operation_args(parser)
    args = parser.parse_args()
    return run_operation(AwsOperation.restart_ecs_service(cluster=args.cluster, service=args.service), args)


def run_invoke_lambda() -> int:
    parser = argparse.ArgumentParser(description="Invoke Lambda")
    parser.add_argument("--function-name", required=True)
    parser.add_argument("--payload")
    add_common_operation_args(parser)
    args = parser.parse_args()
    return run_operation(AwsOperation.invoke_lambda(function_name=args.function_name, payload=args.payload), args)


def run_redrive_sqs_dlq() -> int:
    parser = argparse.ArgumentParser(description="Plan SQS DLQ redrive")
    parser.add_argument("--source-arn", required=True)
    parser.add_argument("--destination-arn", required=True)
    parser.add_argument("--environment", required=True)
    add_common_output_args(parser)
    args = parser.parse_args()
    args.profile = None
    args.region = None
    args.execute = False
    args.confirm_resource = None
    return run_operation(AwsOperation.redrive_sqs_plan(source_arn=args.source_arn, destination_arn=args.destination_arn), args)


def run_purge_sqs_queue_plan() -> int:
    parser = argparse.ArgumentParser(description="Plan SQS purge")
    parser.add_argument("--queue-url", required=True)
    parser.add_argument("--environment", required=True)
    add_common_output_args(parser)
    args = parser.parse_args()
    args.profile = None
    args.region = None
    args.execute = False
    args.confirm_resource = None
    return run_operation(AwsOperation.purge_sqs_plan(queue_url=args.queue_url), args)


def run_invalidate_cloudfront() -> int:
    parser = argparse.ArgumentParser(description="Invalidate CloudFront cache")
    parser.add_argument("--distribution-id", required=True)
    parser.add_argument("--paths", required=True)
    add_common_operation_args(parser)
    args = parser.parse_args()
    return run_operation(AwsOperation.invalidate_cloudfront(distribution_id=args.distribution_id, paths=args.paths), args)


def run_scale_asg() -> int:
    parser = argparse.ArgumentParser(description="Scale Auto Scaling Group")
    parser.add_argument("--auto-scaling-group", required=True)
    parser.add_argument("--desired-capacity", required=True, type=int)
    add_common_operation_args(parser)
    args = parser.parse_args()
    return run_operation(AwsOperation.scale_autoscaling_group(auto_scaling_group=args.auto_scaling_group, desired_capacity=args.desired_capacity), args)


def run_toggle_eventbridge_rule() -> int:
    parser = argparse.ArgumentParser(description="Toggle EventBridge rule")
    parser.add_argument("--rule-name", required=True)
    parser.add_argument("--action", required=True, choices=["enable", "disable"])
    add_common_operation_args(parser)
    args = parser.parse_args()
    return run_operation(AwsOperation.toggle_eventbridge_rule(rule_name=args.rule_name, action=args.action), args)


def run_operation_report() -> int:
    parser = argparse.ArgumentParser(description="Generate operation report")
    parser.add_argument("--operation-dir", required=True)
    add_common_output_args(parser)
    args = parser.parse_args()
    try:
        operation_dir = Path(args.operation_dir).expanduser().resolve()
        output_dir = resolve_output_dir(args.output_dir or args.operation_dir, args.yes_create_dir)
        dry_run = load_json(operation_dir / "operation-dry-run.json")
        result = load_json(operation_dir / "operation-result.json")
        write_text(output_dir / "operation-report.md", render_operation_report(dry_run, result), args.yes_overwrite)
        print(json.dumps({"output_dir": str(output_dir), "report": str(output_dir / "operation-report.md")}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
