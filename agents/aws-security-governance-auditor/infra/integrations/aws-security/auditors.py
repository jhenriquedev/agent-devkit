#!/usr/bin/env python3
"""Deterministic AWS security auditors."""

from __future__ import annotations

from typing import Any


def finding(
    *,
    finding_id: str,
    severity: str,
    category: str,
    resource_type: str,
    resource_id: str,
    title: str,
    evidence: str,
    recommendation: str,
    status: str = "confirmed",
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "severity": severity,
        "category": category,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "title": title,
        "evidence": evidence,
        "recommendation": recommendation,
        "status": status,
    }


def audit_iam_principals(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for policy in ((snapshot.get("iam") or {}).get("policies") or []):
        if policy_allows_admin(policy.get("Document") or {}):
            principal = policy.get("Principal") or policy.get("PolicyName") or "unknown"
            findings.append(
                finding(
                    finding_id=f"iam-wildcard-admin-{slug(principal)}",
                    severity="critical",
                    category="iam",
                    resource_type="iam-policy",
                    resource_id=str(principal),
                    title="IAM policy allows wildcard admin access",
                    evidence=f"Policy `{policy.get('PolicyName') or '-'}` contains Allow Action=* Resource=*.",
                    recommendation="Replace wildcard permissions with least-privilege actions and scoped resources.",
                )
            )
    return findings


def audit_public_exposure(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return audit_security_groups(snapshot) + [
        item
        for item in audit_s3_buckets(snapshot)
        if item["id"].startswith("s3-public")
    ]


def audit_security_groups(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for group in snapshot.get("security_groups") or []:
        group_id = group.get("GroupId") or group.get("GroupName") or "unknown"
        for permission in group.get("IpPermissions") or []:
            if permission_public(permission):
                from_port = permission.get("FromPort")
                to_port = permission.get("ToPort")
                severity = "critical" if from_port in {22, 3389} or to_port in {22, 3389} else "high"
                findings.append(
                    finding(
                        finding_id=f"sg-public-{slug(group_id)}-{from_port or 'all'}",
                        severity=severity,
                        category="public-exposure",
                        resource_type="security-group",
                        resource_id=str(group_id),
                        title="Security Group allows public ingress",
                        evidence=f"Security Group `{group.get('GroupName') or group_id}` allows 0.0.0.0/0 or ::/0 on port {from_port or 'all'}.",
                        recommendation="Restrict ingress to required CIDRs, VPN, private networks, or managed front doors.",
                    )
                )
    return findings


def audit_s3_buckets(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for bucket in ((snapshot.get("s3") or {}).get("buckets") or []):
        name = bucket.get("Name") or "unknown-bucket"
        pab = bucket.get("PublicAccessBlock") or {}
        if not pab or not all(bool(pab.get(key)) for key in ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets")):
            findings.append(
                finding(
                    finding_id=f"s3-public-access-block-{slug(name)}",
                    severity="high",
                    category="public-exposure",
                    resource_type="s3-bucket",
                    resource_id=name,
                    title="S3 bucket public access block is incomplete",
                    evidence=f"Bucket `{name}` does not have all public access block flags enabled.",
                    recommendation="Enable all S3 Block Public Access settings unless public hosting is explicitly required and reviewed.",
                )
            )
        if not bucket.get("Encryption"):
            findings.append(
                finding(
                    finding_id=f"s3-encryption-{slug(name)}",
                    severity="medium",
                    category="encryption",
                    resource_type="s3-bucket",
                    resource_id=name,
                    title="S3 bucket encryption not detected",
                    evidence=f"Bucket `{name}` has no encryption metadata in the collected snapshot.",
                    recommendation="Enable default server-side encryption with SSE-S3 or KMS.",
                    status="potential",
                )
            )
    return findings


def audit_secrets_usage(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for secret in ((snapshot.get("secrets") or {}).get("secrets") or []):
        if not secret.get("RotationEnabled"):
            name = secret.get("Name") or secret.get("ARN") or "unknown-secret"
            findings.append(
                finding(
                    finding_id=f"secret-rotation-{slug(name)}",
                    severity="medium",
                    category="secrets",
                    resource_type="secret",
                    resource_id=str(name),
                    title="Secret rotation not detected",
                    evidence=f"Secret `{name}` has no RotationEnabled metadata.",
                    recommendation="Enable rotation for long-lived credentials or document why rotation is not applicable.",
                    status="potential",
                )
            )
    return findings


def audit_encryption(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in audit_s3_buckets(snapshot) if item["category"] == "encryption"]


def audit_cloudtrail_config(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    trails = (snapshot.get("cloudtrail") or {}).get("trails") or []
    if not trails:
        return [
            finding(
                finding_id="cloudtrail-missing",
                severity="critical",
                category="cloudtrail",
                resource_type="account",
                resource_id=str(snapshot.get("account_id") or "unknown-account"),
                title="CloudTrail trail not detected",
                evidence="No CloudTrail trails were present in the collected snapshot.",
                recommendation="Enable organization or account CloudTrail with log validation and centralized storage.",
            )
        ]
    return []


def audit_config_guardrails(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    config = snapshot.get("config") or {}
    if not config.get("recorders"):
        return [
            finding(
                finding_id="aws-config-recorder-missing",
                severity="high",
                category="governance",
                resource_type="account",
                resource_id=str(snapshot.get("account_id") or "unknown-account"),
                title="AWS Config recorder not detected",
                evidence="No AWS Config configuration recorders were present in the collected snapshot.",
                recommendation="Enable AWS Config recorders and managed rules for required governance controls.",
            )
        ]
    return []


def policy_allows_admin(document: dict[str, Any]) -> bool:
    statements = document.get("Statement") or []
    if isinstance(statements, dict):
        statements = [statements]
    for statement in statements:
        if statement.get("Effect") != "Allow":
            continue
        actions = listify(statement.get("Action"))
        resources = listify(statement.get("Resource"))
        if "*" in actions and "*" in resources:
            return True
    return False


def permission_public(permission: dict[str, Any]) -> bool:
    for item in permission.get("IpRanges") or []:
        if item.get("CidrIp") == "0.0.0.0/0":
            return True
    for item in permission.get("Ipv6Ranges") or []:
        if item.get("CidrIpv6") == "::/0":
            return True
    return False


def listify(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def slug(value: Any) -> str:
    text = str(value).lower()
    return "".join(ch if ch.isalnum() else "-" for ch in text).strip("-") or "unknown"
