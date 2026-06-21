#!/usr/bin/env python3
"""Renderers for AWS security governance outputs."""

from __future__ import annotations

from collections import Counter
from typing import Any


def render_findings(title: str, findings: list[dict[str, Any]]) -> str:
    lines = [f"# {title}", ""]
    if not findings:
        lines.append("- Nenhum achado detectado.")
    for item in findings:
        lines.append(f"- [{item.get('severity')}] {item.get('title')} - `{item.get('resource_id')}`")
        lines.append(f"  - Evidencia: {item.get('evidence')}")
        lines.append(f"  - Recomendacao: {item.get('recommendation')}")
    lines.append("")
    return "\n".join(lines)


def render_security_report(findings: list[dict[str, Any]]) -> str:
    counts = Counter(item.get("severity") for item in findings)
    lines = [
        "# AWS Security Governance Report",
        "",
        "## Summary",
        "",
        f"- Findings: {len(findings)}",
    ]
    for severity in ("critical", "high", "medium", "low", "info"):
        lines.append(f"- {severity}: {counts.get(severity, 0)}")
    lines.extend(["", "## Findings", ""])
    if not findings:
        lines.append("- Nenhum achado consolidado.")
    for item in findings:
        lines.append(f"- [{item.get('severity')}] {item.get('title')} ({item.get('category')})")
        lines.append(f"  - Resource: `{item.get('resource_id')}`")
        lines.append(f"  - Evidence: {item.get('evidence')}")
        lines.append(f"  - Recommendation: {item.get('recommendation')}")
    lines.append("")
    return "\n".join(lines)


def render_remediation_plan(findings: list[dict[str, Any]]) -> str:
    lines = [
        "# AWS Security Remediation Plan",
        "",
        "Este plano nao executa correcoes. Use como roteiro manual/revisavel.",
        "",
    ]
    for severity in ("critical", "high", "medium", "low", "info"):
        bucket = [item for item in findings if item.get("severity") == severity]
        if not bucket:
            continue
        lines.extend([f"## {severity.title()}", ""])
        for item in bucket:
            lines.append(f"- {item.get('title')} em `{item.get('resource_id')}`")
            lines.append(f"  - Acao proposta: {item.get('recommendation')}")
            lines.append("  - Validacao: executar nova auditoria read-only apos remediacao.")
    if not findings:
        lines.append("- Nenhuma remediacao proposta.")
    lines.append("")
    return "\n".join(lines)
