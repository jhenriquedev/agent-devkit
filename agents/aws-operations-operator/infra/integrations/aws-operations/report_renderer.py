#!/usr/bin/env python3
"""Render operation plans and reports."""

from __future__ import annotations

from typing import Any


def render_operation_plan(payload: dict[str, Any]) -> str:
    command = payload.get("display_command") or payload.get("aws_command") or []
    return "\n".join(
        [
            "# AWS Operation Plan",
            "",
            f"- Operation: `{payload.get('operation')}`",
            f"- Resource: `{payload.get('resource_id')}`",
            f"- Environment: `{payload.get('environment')}`",
            f"- Region: `{payload.get('region') or '-'}`",
            f"- Profile: `{payload.get('profile') or '-'}`",
            f"- Status: `{payload.get('status')}`",
            f"- Execute: `{payload.get('execute')}`",
            f"- Destructive: `{payload.get('destructive')}`",
            "",
            "## AWS Command",
            "",
            "```bash",
            " ".join(str(part) for part in command),
            "```",
            "",
        ]
    )


def render_rollback_notes(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Rollback Notes",
            "",
            f"- Operation: `{payload.get('operation')}`",
            f"- Resource: `{payload.get('resource_id')}`",
            f"- Guidance: {payload.get('rollback_hint') or 'Validar estado anterior e reexecutar acao reversa quando aplicavel.'}",
            "",
        ]
    )


def render_operation_report(dry_run: dict[str, Any] | None, result: dict[str, Any] | None) -> str:
    source = result or dry_run or {}
    lines = [
        "# AWS Operation Report",
        "",
        f"- Operation: `{source.get('operation') or '-'}`",
        f"- Resource: `{source.get('resource_id') or '-'}`",
        f"- Environment: `{source.get('environment') or '-'}`",
        f"- Region: `{source.get('region') or '-'}`",
        f"- Profile: `{source.get('profile') or '-'}`",
        f"- Status: `{source.get('status') or '-'}`",
        f"- Executed: `{bool(result and result.get('execute'))}`",
        "",
    ]
    if source.get("account_validation"):
        lines.extend(["## Account Validation", "", "```json", compact_json(source.get("account_validation")), "```", ""])
    if source.get("preflight"):
        lines.extend(["## Preflight", "", "```json", compact_json(source.get("preflight")), "```", ""])
    if source.get("post_check"):
        lines.extend(["## Post Check", "", "```json", compact_json(source.get("post_check")), "```", ""])
    if result:
        lines.extend(["## Result", "", "```json", compact_json(safe_result(result)), "```", ""])
    return "\n".join(lines)


def compact_json(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, indent=2)[:4000]


def safe_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "returncode": result.get("returncode"),
        "stdout": result.get("stdout"),
        "lambda_response": result.get("lambda_response"),
    }
