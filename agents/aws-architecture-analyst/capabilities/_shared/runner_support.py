#!/usr/bin/env python3
"""Shared runner support for AWS Architecture Analyst."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
AWS_DIR = AGENT_DIR / "infra" / "integrations" / "aws"

sys.path.insert(0, str(AWS_DIR))

from aws_repository import AwsArchitectureConfig, AwsArchitectureRepository, build_inventory  # pylint: disable=import-error
from dependency_mapper import build_dependency_map, estimate_blast_radius  # pylint: disable=import-error
from normalizers import service_counts  # pylint: disable=import-error
from report_renderer import (  # pylint: disable=import-error
    render_architecture_report,
    render_blast_radius,
    render_dependency_map,
    render_findings,
    render_inventory_summary,
    render_workload_analysis,
)


def add_common_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-dir")
    parser.add_argument("--yes-create-dir", action="store_true")
    parser.add_argument("--yes-overwrite", action="store_true")


def add_inventory_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--inventory", required=True)


def load_json(path: str) -> dict[str, Any]:
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


def print_result(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def print_error(exc: Exception) -> int:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1


def normalize_fixture_inventory(payload: dict[str, Any]) -> dict[str, Any]:
    resources = payload.get("resources") or []
    if "resource_count" in payload and "services" in payload:
        return payload
    return build_inventory(
        account_id=payload.get("account_id"),
        region=payload.get("region") or "unknown",
        resources=resources,
        gaps=payload.get("gaps") or [],
        profile=payload.get("profile"),
    )


def run_discover_inventory() -> int:
    parser = argparse.ArgumentParser(description="Discover AWS account inventory")
    parser.add_argument("--profile")
    parser.add_argument("--region")
    parser.add_argument("--account-id")
    parser.add_argument("--fixture")
    add_common_output_args(parser)
    args = parser.parse_args()
    try:
        if args.fixture:
            inventory = normalize_fixture_inventory(load_json(args.fixture))
        else:
            repo = AwsArchitectureRepository(
                AwsArchitectureConfig(default_region=args.region, profile=args.profile)
            )
            inventory = repo.discover_account_inventory(region=args.region, account_id=args.account_id)
        output_dir = resolve_output_dir(args.output_dir, args.yes_create_dir)
        write_json(output_dir / "inventory.json", inventory, args.yes_overwrite)
        write_text(output_dir / "inventory-summary.md", render_inventory_summary(inventory), args.yes_overwrite)
        write_json(
            output_dir / "collection-metadata.json",
            {
                "account_id": inventory.get("account_id"),
                "region": inventory.get("region"),
                "profile": args.profile or inventory.get("profile"),
                "resource_count": inventory.get("resource_count"),
                "fixture": bool(args.fixture),
            },
            args.yes_overwrite,
        )
        return print_result({"output_dir": str(output_dir), "resource_count": inventory.get("resource_count"), "services": inventory.get("services")})
    except Exception as exc:
        return print_error(exc)


def run_map_dependencies() -> int:
    parser = argparse.ArgumentParser(description="Map AWS service dependencies")
    add_inventory_arg(parser)
    add_common_output_args(parser)
    args = parser.parse_args()
    try:
        inventory = load_json(args.inventory)
        dependency_map = build_dependency_map(inventory.get("resources") or [])
        output_dir = resolve_output_dir(args.output_dir, args.yes_create_dir)
        write_json(output_dir / "dependency-map.json", dependency_map, args.yes_overwrite)
        write_text(output_dir / "dependency-map.md", render_dependency_map(dependency_map), args.yes_overwrite)
        write_json(output_dir / "unresolved-dependencies.json", dependency_map.get("unresolved_dependencies") or [], args.yes_overwrite)
        return print_result({"output_dir": str(output_dir), "edge_count": dependency_map.get("edge_count")})
    except Exception as exc:
        return print_error(exc)


def run_generate_report() -> int:
    parser = argparse.ArgumentParser(description="Generate AWS architecture report")
    add_inventory_arg(parser)
    parser.add_argument("--dependency-map")
    add_common_output_args(parser)
    args = parser.parse_args()
    try:
        inventory = load_json(args.inventory)
        dependency_map = load_json(args.dependency_map) if args.dependency_map else build_dependency_map(inventory.get("resources") or [])
        output_dir = resolve_output_dir(args.output_dir, args.yes_create_dir)
        report = render_architecture_report(inventory, dependency_map)
        write_text(output_dir / "architecture-report.md", report, args.yes_overwrite)
        write_text(output_dir / "executive-summary.md", render_inventory_summary(inventory), args.yes_overwrite)
        write_text(output_dir / "recommended-actions.md", render_recommendations(inventory, dependency_map), args.yes_overwrite)
        write_text(output_dir / "open-questions.md", render_open_questions(), args.yes_overwrite)
        return print_result({"output_dir": str(output_dir), "report": str(output_dir / "architecture-report.md")})
    except Exception as exc:
        return print_error(exc)


def run_workload_analysis() -> int:
    parser = argparse.ArgumentParser(description="Analyze AWS workload architecture")
    add_inventory_arg(parser)
    parser.add_argument("--workload")
    parser.add_argument("--resource-prefix")
    add_common_output_args(parser)
    args = parser.parse_args()
    try:
        inventory = load_json(args.inventory)
        resources = filter_workload(inventory.get("resources") or [], args.workload, args.resource_prefix)
        output_dir = resolve_output_dir(args.output_dir, args.yes_create_dir)
        write_json(output_dir / "workload-components.json", {"resources": resources, "services": service_counts(resources)}, args.yes_overwrite)
        write_text(output_dir / "workload-architecture.md", render_workload_analysis(resources, args.workload or args.resource_prefix), args.yes_overwrite)
        write_text(output_dir / "workload-open-questions.md", "- Confirmar criticidade e owners do workload.\n", args.yes_overwrite)
        return print_result({"output_dir": str(output_dir), "resource_count": len(resources)})
    except Exception as exc:
        return print_error(exc)


def run_review(kind: str) -> int:
    parser = argparse.ArgumentParser(description=f"Review AWS {kind}")
    add_inventory_arg(parser)
    add_common_output_args(parser)
    args = parser.parse_args()
    try:
        inventory = load_json(args.inventory)
        findings = build_findings(kind, inventory.get("resources") or [])
        output_dir = resolve_output_dir(args.output_dir, args.yes_create_dir)
        json_name = f"{kind}-findings.json"
        md_name = f"{kind}-review.md"
        write_json(output_dir / json_name, {"findings": findings}, args.yes_overwrite)
        write_text(output_dir / md_name, render_findings(f"AWS {kind.title()} Review", findings), args.yes_overwrite)
        return print_result({"output_dir": str(output_dir), "finding_count": len(findings)})
    except Exception as exc:
        return print_error(exc)


def run_blast_radius() -> int:
    parser = argparse.ArgumentParser(description="Estimate AWS blast radius")
    parser.add_argument("--resource-id", required=True)
    add_inventory_arg(parser)
    parser.add_argument("--dependency-map")
    add_common_output_args(parser)
    args = parser.parse_args()
    try:
        inventory = load_json(args.inventory)
        dependency_map = load_json(args.dependency_map) if args.dependency_map else build_dependency_map(inventory.get("resources") or [])
        result = estimate_blast_radius(resource_id=args.resource_id, resources=inventory.get("resources") or [], dependency_map=dependency_map)
        output_dir = resolve_output_dir(args.output_dir, args.yes_create_dir)
        write_json(output_dir / "blast-radius.json", result, args.yes_overwrite)
        write_text(output_dir / "blast-radius.md", render_blast_radius(result), args.yes_overwrite)
        return print_result({"output_dir": str(output_dir), "direct_count": result.get("direct_count")})
    except Exception as exc:
        return print_error(exc)


def filter_workload(resources: list[dict[str, Any]], workload: str | None, prefix: str | None) -> list[dict[str, Any]]:
    if not workload and not prefix:
        return resources
    needle = (workload or prefix or "").lower()
    return [
        resource
        for resource in resources
        if needle in str(resource.get("name", "")).lower() or needle in str(resource.get("id", "")).lower()
    ]


def build_findings(kind: str, resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if kind == "resilience":
        for resource in resources:
            attrs = resource.get("attributes") or {}
            if resource.get("service") == "sqs":
                if "has_dlq" not in attrs:
                    findings.append({
                        "severity": "gap",
                        "message": (
                            f"SQS `{resource.get('name')}`: atributo `has_dlq` ausente no inventario. "
                            "Execute `sqs.get-queue-attributes` para avaliar resiliencia."
                        ),
                        "confidence": "unknown",
                    })
                elif not attrs.get("has_dlq"):
                    findings.append({
                        "severity": "medium",
                        "message": f"SQS `{resource.get('name')}` sem DLQ confirmada.",
                        "confidence": "confirmed",
                    })
            if resource.get("service") == "lambda":
                if "vpc_attached" not in attrs:
                    findings.append({
                        "severity": "gap",
                        "message": (
                            f"Lambda `{resource.get('name')}`: atributo `vpc_attached` ausente no inventario. "
                            "Verifique VpcConfig no collector lambda."
                        ),
                        "confidence": "unknown",
                    })
                elif not attrs.get("vpc_attached"):
                    findings.append({
                        "severity": "info",
                        "message": f"Lambda `{resource.get('name')}` sem VPC anexada; validar se e esperado.",
                        "confidence": "confirmed",
                    })
    elif kind == "observability":
        has_alarms = any(resource.get("service") == "cloudwatch" and resource.get("resource_type") == "alarm" for resource in resources)
        if not has_alarms:
            findings.append({
                "severity": "medium",
                "message": "Nenhum CloudWatch alarm detectado no inventario.",
                "confidence": "confirmed",
            })
    elif kind == "networking":
        for resource in resources:
            attrs = resource.get("attributes") or {}
            if resource.get("service") == "ec2":
                if "public_ip" not in attrs:
                    findings.append({
                        "severity": "gap",
                        "message": (
                            f"EC2 `{resource.get('name')}`: atributo `public_ip` ausente no inventario. "
                            "Ampliar collector ec2.describe-instances para coletar `PublicIpAddress`."
                        ),
                        "confidence": "unknown",
                    })
                elif attrs.get("public_ip"):
                    findings.append({
                        "severity": "medium",
                        "message": f"EC2 `{resource.get('name')}` possui IP publico.",
                        "confidence": "confirmed",
                    })
    return findings


def render_recommendations(inventory: dict[str, Any], dependency_map: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Recommended Actions",
            "",
            "- Revisar dependencias com baixa confianca antes de qualquer mudanca.",
            "- Completar tags de ownership, ambiente e criticidade nos recursos sem metadados.",
            f"- Validar {len(dependency_map.get('unresolved_dependencies') or [])} dependencias nao resolvidas.",
            "",
        ]
    )


def render_open_questions() -> str:
    return "\n".join(
        [
            "# Open Questions",
            "",
            "- Quais workloads sao criticos para producao?",
            "- Quais recursos possuem owners definidos?",
            "- Existem dependencias externas fora da conta AWS inventariada?",
            "",
        ]
    )
