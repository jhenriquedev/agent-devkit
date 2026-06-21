#!/usr/bin/env python3
"""Markdown renderers for AWS architecture artifacts."""

from __future__ import annotations

from collections import Counter
from typing import Any


def render_inventory_summary(inventory: dict[str, Any]) -> str:
    lines = [
        "# AWS Inventory Summary",
        "",
        f"- Account: `{inventory.get('account_id') or '-'}`",
        f"- Region: `{inventory.get('region') or '-'}`",
        f"- Resources: {inventory.get('resource_count', 0)}",
        "",
        "## Services",
        "",
    ]
    services = inventory.get("services") or {}
    if services:
        lines.extend(f"- {service}: {count}" for service, count in services.items())
    else:
        lines.append("- Nenhum recurso detectado.")
    lines.append("")
    return "\n".join(lines)


def render_dependency_map(dependency_map: dict[str, Any]) -> str:
    lines = [
        "# AWS Dependency Map",
        "",
        f"- Nodes: {len(dependency_map.get('nodes') or [])}",
        f"- Edges: {dependency_map.get('edge_count', 0)}",
        "",
        "## Edges",
        "",
    ]
    for edge in dependency_map.get("edges") or []:
        lines.append(
            f"- `{edge.get('source_id')}` -> `{edge.get('target_id')}` "
            f"({edge.get('type')}, {edge.get('confidence')})"
        )
    if not dependency_map.get("edges"):
        lines.append("- Nenhuma dependencia detectada.")
    lines.append("")
    return "\n".join(lines)


def render_architecture_report(inventory: dict[str, Any], dependency_map: dict[str, Any] | None = None) -> str:
    dependency_map = dependency_map or {"edges": [], "edge_count": 0}
    resources = inventory.get("resources") or []
    lines = [
        "# AWS Architecture Report",
        "",
        "## Executive Summary",
        "",
        f"A conta `{inventory.get('account_id') or '-'}` na regiao `{inventory.get('region') or '-'}` possui "
        f"{inventory.get('resource_count', len(resources))} recursos inventariados.",
        "",
        "## Services",
        "",
    ]
    services = inventory.get("services") or {}
    lines.extend(f"- {service}: {count}" for service, count in services.items())
    if not services:
        lines.append("- Nenhum servico inventariado.")
    lines.extend(["", "## Key Resources", ""])
    for resource in resources[:30]:
        lines.append(f"- `{resource.get('name')}` ({resource.get('service')}/{resource.get('resource_type')})")
    if not resources:
        lines.append("- Nenhum recurso.")
    lines.extend(["", "## Dependencies", ""])
    for edge in (dependency_map.get("edges") or [])[:30]:
        lines.append(
            f"- `{edge.get('source_id')}` {edge.get('type')} `{edge.get('target_id')}` "
            f"[{edge.get('confidence')}]"
        )
    if not dependency_map.get("edges"):
        lines.append("- Nenhuma dependencia mapeada.")
    lines.extend(
        [
            "",
            "## Open Questions",
            "",
            "- Validar ownership, criticidade e ambiente dos workloads inventariados.",
            "- Confirmar dependencias inferidas antes de qualquer operacao em producao.",
            "",
        ]
    )
    return "\n".join(lines)


def render_findings(title: str, findings: list[dict[str, Any]]) -> str:
    lines = [f"# {title}", ""]
    if not findings:
        lines.append("- Nenhum achado gerado a partir do inventario atual.")
    for finding in findings:
        lines.append(f"- [{finding.get('severity', 'info')}] {finding.get('message')}")
    lines.append("")
    return "\n".join(lines)


def render_workload_analysis(resources: list[dict[str, Any]], workload: str | None) -> str:
    counts = Counter(item.get("service") or "unknown" for item in resources)
    lines = [
        "# Workload Architecture",
        "",
        f"- Workload: `{workload or 'auto'}`",
        f"- Resources: {len(resources)}",
        "",
        "## Components",
        "",
    ]
    lines.extend(f"- {service}: {count}" for service, count in sorted(counts.items()))
    if not resources:
        lines.append("- Nenhum recurso encontrado para o filtro informado.")
    lines.extend(["", "## Open Questions", "", "- Confirmar se o filtro representa todo o workload."])
    return "\n".join(lines) + "\n"


def render_blast_radius(result: dict[str, Any]) -> str:
    lines = [
        "# Blast Radius",
        "",
        f"- Resource: `{result.get('resource_id')}`",
        f"- Direct dependents: {result.get('direct_count', 0)}",
        f"- Indirect dependents: {result.get('indirect_count', 0)}",
        "",
        "## Direct Dependents",
        "",
    ]
    lines.extend(f"- `{item}`" for item in result.get("direct_dependents") or [])
    if not result.get("direct_dependents"):
        lines.append("- Nenhum dependente direto detectado.")
    lines.extend(["", "## Unsafe Actions", ""])
    lines.extend(f"- {item}" for item in result.get("unsafe_actions") or [])
    lines.append("")
    return "\n".join(lines)
