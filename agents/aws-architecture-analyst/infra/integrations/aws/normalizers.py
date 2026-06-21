#!/usr/bin/env python3
"""Normalizers for AWS architecture inventory resources."""

from __future__ import annotations

from collections import Counter
from typing import Any


def base_resource(
    *,
    resource_id: str,
    arn: str | None,
    name: str,
    service: str,
    resource_type: str,
    region: str,
    account_id: str | None,
    tags: dict[str, str] | None = None,
    relationships: list[dict[str, Any]] | None = None,
    attributes: dict[str, Any] | None = None,
    source_method: str,
) -> dict[str, Any]:
    return {
        "id": resource_id,
        "arn": arn,
        "name": name,
        "service": service,
        "resource_type": resource_type,
        "region": region,
        "account_id": account_id,
        "tags": tags or {},
        "relationships": relationships or [],
        "attributes": attributes or {},
        "raw_ref": {"source_method": source_method},
    }


def normalize_lambda_function(item: dict[str, Any], *, account_id: str | None, region: str) -> dict[str, Any]:
    arn = item.get("FunctionArn")
    role = item.get("Role")
    relationships = []
    if role:
        relationships.append(
            {
                "target_id": role,
                "type": "uses-role",
                "confidence": "confirmed",
                "evidence": "Lambda Role field",
            }
        )
    vpc_config = item.get("VpcConfig") or {}
    for subnet_id in vpc_config.get("SubnetIds") or []:
        relationships.append(
            {
                "target_id": subnet_id,
                "type": "runs-in-subnet",
                "confidence": "confirmed",
                "evidence": "Lambda VpcConfig.SubnetIds",
            }
        )
    for security_group_id in vpc_config.get("SecurityGroupIds") or []:
        relationships.append(
            {
                "target_id": security_group_id,
                "type": "uses-security-group",
                "confidence": "confirmed",
                "evidence": "Lambda VpcConfig.SecurityGroupIds",
            }
        )
    return base_resource(
        resource_id=arn or item.get("FunctionName") or "unknown-lambda",
        arn=arn,
        name=item.get("FunctionName") or arn or "unknown-lambda",
        service="lambda",
        resource_type="function",
        region=region,
        account_id=account_id,
        relationships=relationships,
        attributes={
            "runtime": item.get("Runtime"),
            "handler": item.get("Handler"),
            "memory_size": item.get("MemorySize"),
            "timeout": item.get("Timeout"),
            "vpc_attached": bool(vpc_config),
        },
        source_method="lambda.list-functions",
    )


def normalize_generic_resource(
    *,
    service: str,
    resource_type: str,
    resource_id: str,
    name: str,
    region: str,
    account_id: str | None,
    arn: str | None = None,
    attributes: dict[str, Any] | None = None,
    relationships: list[dict[str, Any]] | None = None,
    source_method: str,
) -> dict[str, Any]:
    return base_resource(
        resource_id=resource_id,
        arn=arn,
        name=name,
        service=service,
        resource_type=resource_type,
        region=region,
        account_id=account_id,
        relationships=relationships,
        attributes=attributes,
        source_method=source_method,
    )


def service_counts(resources: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(item.get("service") or "unknown" for item in resources).items()))
