#!/usr/bin/env python3
"""Shared runner support for AWS Security Governance Auditor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
AWS_DIR = AGENT_DIR / "infra" / "integrations" / "aws-security"

sys.path.insert(0, str(AWS_DIR))

from auditors import (  # pylint: disable=import-error
    audit_cloudtrail_config,
    audit_config_guardrails,
    audit_encryption,
    audit_iam_principals,
    audit_public_exposure,
    audit_s3_buckets,
    audit_secrets_usage,
    audit_security_groups,
)
from aws_security_repository import AwsSecurityConfig, AwsSecurityRepository  # pylint: disable=import-error
from report_renderer import render_findings, render_remediation_plan, render_security_report  # pylint: disable=import-error


AUDITORS: dict[str, tuple[Callable[[dict[str, Any]], list[dict[str, Any]]], str, str, str]] = {
    "iam": (audit_iam_principals, "iam-audit.json", "iam-audit.md", "IAM Audit"),
    "public-exposure": (audit_public_exposure, "public-exposure.json", "public-exposure.md", "Public Exposure Audit"),
    "security-groups": (audit_security_groups, "security-groups-audit.json", "security-groups-audit.md", "Security Groups Audit"),
    "s3-buckets": (audit_s3_buckets, "s3-buckets-audit.json", "s3-buckets-audit.md", "S3 Buckets Audit"),
    "secrets": (audit_secrets_usage, "secrets-usage-audit.json", "secrets-usage-audit.md", "Secrets Usage Audit"),
    "encryption": (audit_encryption, "encryption-audit.json", "encryption-audit.md", "Encryption Audit"),
    "cloudtrail": (audit_cloudtrail_config, "cloudtrail-audit.json", "cloudtrail-audit.md", "CloudTrail Audit"),
    "config": (audit_config_guardrails, "config-guardrails-audit.json", "config-guardrails-audit.md", "AWS Config Guardrails Audit"),
}


def add_common_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile")
    parser.add_argument("--region")
    parser.add_argument("--fixture")


def add_common_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-dir")
    parser.add_argument("--yes-create-dir", action="store_true")
    parser.add_argument("--yes-overwrite", action="store_true")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any, overwrite: bool) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", overwrite)


def write_text(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise ValueError(f"artifact already exists; pass --yes-overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def resolve_output_dir(output_dir: str | None, create: bool) -> Path:
    path = Path(output_dir or ".").expanduser().resolve()
    if not path.exists():
        if not create:
            raise ValueError(f"output directory does not exist; pass --yes-create-dir: {path}")
        path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise ValueError(f"output path is not a directory: {path}")
    return path


def load_snapshot(args: argparse.Namespace) -> dict[str, Any]:
    if args.fixture:
        return load_json(args.fixture)
    return AwsSecurityRepository(
        AwsSecurityConfig(default_region=args.region, profile=args.profile)
    ).collect_security_snapshot(region=args.region)


def run_audit(audit_key: str) -> int:
    parser = argparse.ArgumentParser(description=f"Run AWS security audit: {audit_key}")
    add_common_source_args(parser)
    add_common_output_args(parser)
    args = parser.parse_args()
    try:
        auditor, json_name, md_name, title = AUDITORS[audit_key]
        snapshot = load_snapshot(args)
        findings = auditor(snapshot)
        output_dir = resolve_output_dir(args.output_dir, args.yes_create_dir)
        payload = {
            "account_id": snapshot.get("account_id"),
            "region": snapshot.get("region"),
            "audit": audit_key,
            "finding_count": len(findings),
            "findings": findings,
        }
        write_json(output_dir / json_name, payload, args.yes_overwrite)
        write_text(output_dir / md_name, render_findings(title, findings), args.yes_overwrite)
        return print_result({"output_dir": str(output_dir), "finding_count": len(findings)})
    except Exception as exc:
        return print_error(exc)


def run_security_report() -> int:
    parser = argparse.ArgumentParser(description="Generate AWS security report")
    parser.add_argument("--audit-dir", required=True)
    add_common_output_args(parser)
    args = parser.parse_args()
    try:
        findings = collect_findings(Path(args.audit_dir))
        output_dir = resolve_output_dir(args.output_dir or args.audit_dir, args.yes_create_dir)
        payload = {"finding_count": len(findings), "findings": findings}
        write_json(output_dir / "security-findings.json", payload, args.yes_overwrite)
        write_text(output_dir / "security-report.md", render_security_report(findings), args.yes_overwrite)
        return print_result({"output_dir": str(output_dir), "finding_count": len(findings)})
    except Exception as exc:
        return print_error(exc)


def run_remediation_plan() -> int:
    parser = argparse.ArgumentParser(description="Generate AWS security remediation plan")
    parser.add_argument("--audit-dir", required=True)
    add_common_output_args(parser)
    args = parser.parse_args()
    try:
        findings = collect_findings(Path(args.audit_dir))
        output_dir = resolve_output_dir(args.output_dir or args.audit_dir, args.yes_create_dir)
        write_text(output_dir / "remediation-plan.md", render_remediation_plan(findings), args.yes_overwrite)
        return print_result({"output_dir": str(output_dir), "finding_count": len(findings), "execution": "unsupported"})
    except Exception as exc:
        return print_error(exc)


def collect_findings(audit_dir: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in sorted(audit_dir.glob("*.json")):
        if path.name == "security-findings.json":
            continue
        payload = load_json(path)
        for item in payload.get("findings") or []:
            findings.append(item)
    return findings


def print_result(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def print_error(exc: Exception) -> int:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1
