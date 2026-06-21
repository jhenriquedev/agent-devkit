#!/usr/bin/env python3
"""Shared helpers for N1 Support Agent runners."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcc_knowledge import (  # noqa: E402
    build_diagnostic_gaps,
    build_evidence_ledger,
    evaluate_quality_gate,
    route_customer_symptom,
)


ROOT = Path(__file__).resolve().parents[4]
CLI = ROOT / "ai-devkit"
DEFAULT_ANALYSIS_TAG = "Analise N1"


def load_fixture(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_output(content: str, output: str | None) -> None:
    if output:
        Path(output).write_text(content, encoding="utf-8")
    else:
        print(content)


def print_error(exc: Exception) -> int:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1


def run_ai_devkit(args: list[str]) -> str:
    process = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or f"ai-devkit failed: {' '.join(args)}")
    return process.stdout


def run_ai_devkit_json(args: list[str]) -> dict[str, Any]:
    return json.loads(run_ai_devkit(args))


def read_azure_card(project: str, card_id: int, fixture: str | None = None) -> tuple[str, dict[str, Any]]:
    if fixture:
        payload = load_fixture(fixture)
        work_item = payload.get("work_item") or payload.get("card") or {}
        markdown = render_fixture_card(work_item, payload.get("comments"))
        return markdown, card_from_work_item(project, card_id, work_item)

    markdown = run_ai_devkit(
        [
            "run",
            "azure-devops-orchestrator",
            "read-card",
            "--project",
            project,
            "--id",
            str(card_id),
            "--include-comments",
        ]
    )
    return markdown, card_from_markdown(project, card_id, markdown)


def run_restrictive_base_check(card_markdown: str, fixture: str | None = None) -> dict[str, Any] | None:
    cpf = first_match(card_markdown, r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
    if not cpf:
        return None
    command = [
        "run",
        "n1-support-agent",
        "analyze-restrictive-base",
        "--cpf",
        cpf,
        "--format",
        "json",
    ]
    if fixture:
        payload = load_fixture(fixture)
        restrictive_fixture = payload.get("restrictive_base")
        if not restrictive_fixture:
            return unavailable_restrictive_check(cpf, "Restrictive-base fixture was not provided")
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as file:
            json.dump({**restrictive_fixture, "cpf": cpf}, file, ensure_ascii=False)
            temporary_fixture = file.name
        command.extend(["--fixture", temporary_fixture])
    try:
        return run_ai_devkit_json(command)
    except Exception as exc:
        return unavailable_restrictive_check(cpf, truncate(str(exc), 240))
    finally:
        if fixture and "temporary_fixture" in locals():
            Path(temporary_fixture).unlink(missing_ok=True)


def run_bpo_proposal_check(card_markdown: str, fixture: str | None = None) -> dict[str, Any] | None:
    cpf = first_match(card_markdown, r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
    proposal = first_match(card_markdown, r"(?i)\b(?:proposta|proposal)\D{0,20}(\d{4,})\b")
    if not (cpf or proposal):
        return None
    command = [
        "run",
        "n1-support-agent",
        "analyze-bpo-proposal",
        "--format",
        "json",
    ]
    if proposal:
        command.extend(["--proposal-number", proposal])
    if cpf:
        command.extend(["--cpf", cpf])
    if fixture:
        command.extend(["--fixture", fixture])
    try:
        return run_ai_devkit_json(command)
    except Exception as exc:
        return unavailable_bpo_check(proposal=proposal, cpf=cpf, reason=truncate(str(exc), 240))


def unavailable_bpo_check(proposal: str | None, cpf: str | None, reason: str) -> dict[str, Any]:
    return {
        "capability": "analyze-bpo-proposal",
        "status": "unavailable",
        "checkStatus": "unavailable",
        "reason": reason,
        "agent": "n1-support-agent",
        "orchestratedAgent": "bpo-analyser",
        "orchestratedCapability": "analyze-proposal" if proposal else "analyze-cpf-proposals",
        "facts": {
            "proposalNumber": proposal,
            "cpfMasked": mask_cpf(cpf) if cpf else None,
        },
        "attentionPoints": [],
        "hasBlockingSignals": False,
        "rawEvidenceSummary": [],
        "errors": [{"error": reason}],
    }


def unavailable_restrictive_check(cpf: str, reason: str) -> dict[str, Any]:
    return {
        "capability": "analyze-restrictive-base",
        "status": "unavailable",
        "checkStatus": "unavailable",
        "cpfMasked": mask_cpf(cpf),
        "reason": reason,
        "agent": "n1-support-agent",
        "orchestratedAgent": "sqlserver-data-analyzer",
        "orchestratedCapability": "run-readonly-query",
        "candidatesChecked": [],
        "findings": [],
        "errors": [{"error": reason}],
    }


def plan_or_apply_azure_actions(
    *,
    project: str,
    card_id: int,
    tag: str,
    target_state: str | None,
    target_column: str | None,
    current_state: str | None,
    reason: str | None,
    execute: bool,
    fixture: str | None,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    actions.append(
        run_azure_action(
            name="add-analysis-tag",
            capability="update-card-tags",
            args=[
                "--project",
                project,
                "--id",
                str(card_id),
                "--add-tag",
                tag,
                "--reason",
                reason or "N1 analysis started",
            ],
            execute=execute,
            fixture=fixture,
        )
    )
    if target_column or target_state:
        state = target_state or current_state
        if not state:
            raise ValueError("--target-state is required when current card state cannot be inferred")
        move_args = [
            "--project",
            project,
            "--id",
            str(card_id),
            "--state",
            state,
        ]
        if target_column:
            move_args.extend(["--board-column", target_column])
        if reason:
            move_args.extend(["--reason", reason])
        actions.append(
            run_azure_action(
                name="move-card",
                capability="move-card",
                args=move_args,
                execute=execute,
                fixture=fixture,
            )
        )
    return actions


def run_azure_action(
    *,
    name: str,
    capability: str,
    args: list[str],
    execute: bool,
    fixture: str | None,
) -> dict[str, Any]:
    command = ["run", "azure-devops-orchestrator", capability, *args]
    if fixture:
        command.extend(["--fixture", fixture])
    if execute:
        command.append("--execute")
    output = run_ai_devkit(command)
    return {
        "id": name,
        "agent": "azure-devops-orchestrator",
        "capability": capability,
        "mode": "executed" if execute else "dry_run",
        "status": "completed",
        "outputPreview": truncate(output),
    }


def build_contract(
    *,
    project: str,
    card_id: int,
    card: dict[str, Any],
    card_markdown: str,
    azure_actions: list[dict[str, Any]],
    execute: bool,
    tag: str,
    target_column: str | None,
    restrictive_check: dict[str, Any] | None = None,
    bpo_check: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entities = extract_entities(card_markdown)
    symptom_route = route_customer_symptom(card_markdown, entities)
    checks = build_checks(entities, restrictive_check=restrictive_check, bpo_check=bpo_check)
    decision = decide(entities, checks, symptom_route=symptom_route)
    artifacts = build_artifacts(card, entities, decision, checks)
    diagnostic_gaps = [
        *symptom_route.get("diagnosticGaps", []),
        *build_diagnostic_gaps(checks=checks, symptom_route=symptom_route),
    ]
    evidence_ledger = build_evidence_ledger(checks=checks, symptom_route=symptom_route)
    quality_gate = evaluate_quality_gate(entities=entities, checks=checks, symptom_route=symptom_route)
    return {
        "runbook": "n1-card-operational-triage",
        "version": "0.1.0",
        "input": {
            "project": project,
            "card": card_id,
            "execute": execute,
            "analysisTag": tag,
            "targetColumn": target_column,
        },
        "card": card,
        "entities": entities,
        "symptomRoute": symptom_route,
        "checks": checks,
        "evidenceLedger": evidence_ledger,
        "businessRulesApplied": symptom_route.get("businessRules") or [],
        "diagnosticGaps": diagnostic_gaps,
        "qualityGate": quality_gate,
        "decision": decision,
        "recommendedAction": recommended_action(decision),
        "azureActions": azure_actions,
        "artifacts": artifacts,
        "audit": {
            "executedAt": datetime.now(timezone.utc).isoformat(),
            "orchestratedAgents": sorted(
                {item["agent"] for item in azure_actions}
                | {"azure-devops-orchestrator"}
                | ({restrictive_check.get("orchestratedAgent")} if restrictive_check else set())
                | ({bpo_check.get("orchestratedAgent")} if bpo_check else set())
            ),
            "dataSources": [
                "azure-devops",
                *([] if not restrictive_check else ["sqlserver"]),
                *([] if not bpo_check else ["bpo"]),
            ],
            "pendingDataSources": pending_sources(checks),
        },
    }


def render_contract_markdown(contract: dict[str, Any], card_markdown: str) -> str:
    lines = [
        "# N1 Card Runbook",
        "",
        "## Card",
        "",
        f"- Project: {value_or_dash(contract['card'].get('project'))}",
        f"- ID: {value_or_dash(contract['card'].get('id'))}",
        f"- Title: {value_or_dash(contract['card'].get('title'))}",
        f"- State: {value_or_dash(contract['card'].get('state'))}",
        f"- Column: {value_or_dash(contract['card'].get('column'))}",
        "",
        "## Entities",
        "",
        f"- CPF: {value_or_dash(contract['entities'].get('cpfMasked'))}",
        f"- Proposal: {value_or_dash(contract['entities'].get('proposalNumber'))}",
        f"- Contract: {value_or_dash(contract['entities'].get('contractNumber'))}",
        f"- TOPdesk: {value_or_dash(contract['entities'].get('topdeskTicket'))}",
        f"- Request ID: {value_or_dash(contract['entities'].get('requestId'))}",
        "",
        "## Symptom Route",
        "",
        f"- Route: {value_or_dash(contract.get('symptomRoute', {}).get('routeId'))}",
        f"- Domain: {value_or_dash(contract.get('symptomRoute', {}).get('domain'))}",
        f"- Confidence: {value_or_dash(contract.get('symptomRoute', {}).get('confidence'))}",
        "",
        "## Checks",
        "",
    ]
    for check in contract["checks"]:
        lines.append(
            f"- {check['id']}: {check['status']} "
            f"({check.get('agent', '-')}/{check.get('capability', '-')})"
        )
    lines.extend(
        [
            "",
            "## Business Rules",
            "",
        ]
    )
    for rule in contract.get("businessRulesApplied", [])[:8]:
        lines.append(f"- {rule.get('id')}: {rule.get('supportImpact') or rule.get('rule')}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: {contract['decision']['status']}",
            f"- Category: {contract['decision']['category']}",
            f"- Confidence: {contract['decision']['confidence']}",
            f"- Summary: {contract['decision']['summary']}",
            "",
            "## Azure Actions",
            "",
        ]
    )
    for action in contract["azureActions"]:
        lines.append(f"- {action['id']}: {action['mode']} / {action['status']}")
    lines.extend(
        [
            "",
            "## Card Snapshot",
            "",
            card_markdown.strip(),
            "",
            "## N1 Contract",
            "",
            "```json",
            json.dumps(contract, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_fixture_card(work_item: dict[str, Any], comments: Any) -> str:
    comments_list = (comments or {}).get("comments", []) if isinstance(comments, dict) else comments or []
    relations = work_item.get("relations") or []
    attachments = [item for item in relations if item.get("rel") == "AttachedFile"]
    lines = [
        "# Card Analysis",
        "",
        "## Identification",
        "",
        f"- ID: {value_or_dash(work_item.get('id'))}",
        f"- Type: {value_or_dash(work_item.get('work_item_type'))}",
        f"- Title: {value_or_dash(work_item.get('title'))}",
        f"- State: {value_or_dash(work_item.get('state'))}",
        f"- Current column: {value_or_dash(work_item.get('board_column'))}",
        f"- Created at: {value_or_dash(work_item.get('created_date'))}",
        f"- Changed at: {value_or_dash(work_item.get('changed_date'))}",
        f"- Assigned to: {value_or_dash(work_item.get('assigned_to'))}",
        f"- Tags: {', '.join(work_item.get('tags') or []) or '-'}",
        "",
        "## Collected Facts",
        "",
        f"- Description: {clean_text(work_item.get('description')) or '-'}",
        "",
        "## Attachments",
        "",
    ]
    if attachments:
        for attachment in attachments:
            attrs = attachment.get("attributes") or {}
            lines.append(f"- {value_or_dash(attrs.get('name'))}")
    else:
        lines.append("- No attachments found.")
    lines.extend(["", "## Relevant Comments", ""])
    if comments_list:
        for comment in comments_list:
            lines.append(f"- {value_or_dash(comment.get('created_at'))} - {value_or_dash(comment.get('author'))}: {clean_text(comment.get('text'))}")
    else:
        lines.append("- No comments loaded.")
    return "\n".join(lines).rstrip() + "\n"


def card_from_work_item(project: str, card_id: int, work_item: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": project,
        "id": work_item.get("id") or card_id,
        "title": work_item.get("title"),
        "state": work_item.get("state"),
        "column": work_item.get("board_column"),
        "tags": work_item.get("tags") or [],
        "assignedTo": work_item.get("assigned_to"),
        "createdAt": work_item.get("created_date"),
        "changedAt": work_item.get("changed_date"),
    }


def card_from_markdown(project: str, card_id: int, markdown: str) -> dict[str, Any]:
    tags = parse_field(markdown, "Tags")
    return {
        "project": project,
        "id": int(parse_field(markdown, "ID") or card_id),
        "title": parse_field(markdown, "Title"),
        "state": parse_field(markdown, "State"),
        "column": parse_field(markdown, "Current column"),
        "tags": [] if not tags or tags == "-" else [item.strip() for item in tags.split(",") if item.strip()],
        "assignedTo": parse_field(markdown, "Assigned to"),
        "createdAt": parse_field(markdown, "Created at"),
        "changedAt": parse_field(markdown, "Changed at"),
    }


def parse_field(markdown: str, label: str) -> str | None:
    match = re.search(rf"^- {re.escape(label)}:\s*(.+)$", markdown, re.M)
    if not match:
        return None
    value = match.group(1).strip()
    return None if value == "-" else value


def extract_entities(text: str) -> dict[str, Any]:
    cpf = first_match(text, r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
    proposal = first_match(text, r"(?i)\b(?:proposta|proposal)\D{0,20}(\d{4,})\b")
    contract = first_match(text, r"(?i)\b(?:contrato|contract)\D{0,20}([A-Za-z0-9-]{4,})\b")
    topdesk = first_match(text, r"\b(?:T|I)\s?\d{4}[- ]?\d{3,}\b")
    request_id = first_match(text, r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
    return {
        "cpfMasked": mask_cpf(cpf) if cpf else None,
        "cpfPresent": bool(cpf),
        "proposalNumber": proposal,
        "contractNumber": contract,
        "topdeskTicket": topdesk,
        "requestId": request_id,
        "correlationId": request_id,
    }


def first_match(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    if not match:
        return None
    return match.group(1) if match.lastindex else match.group(0)


def mask_cpf(value: str) -> str:
    if "***" in str(value or ""):
        return str(value)
    digits = re.sub(r"\D", "", value)
    if len(digits) != 11:
        return "***"
    return f"{digits[:3]}.***.***-{digits[-2:]}"


def build_checks(
    entities: dict[str, Any],
    *,
    restrictive_check: dict[str, Any] | None = None,
    bpo_check: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    has_customer_ref = bool(entities.get("cpfPresent") or entities.get("proposalNumber"))
    restrictive_status = "ready_to_execute" if entities.get("cpfPresent") else "skipped"
    restrictive_reason = "requires CPF" if not entities.get("cpfPresent") else "CPF extracted from card"
    restrictive_details: dict[str, Any] = {}
    if restrictive_check:
        restrictive_status = restrictive_check.get("checkStatus") or restrictive_check.get("status") or "unavailable"
        restrictive_reason = restrictive_check.get("reason") or restrictive_reason
        restrictive_details = {
            "cpfMasked": restrictive_check.get("cpfMasked"),
            "findings": len(restrictive_check.get("findings") or []),
            "candidatesChecked": len(restrictive_check.get("candidatesChecked") or []),
        }
    bpo_status = "ready_to_execute" if has_customer_ref else "skipped"
    bpo_reason = "requires CPF or proposal number" if not has_customer_ref else "CPF or proposal extracted from card"
    bpo_details: dict[str, Any] = {}
    if bpo_check:
        bpo_status = bpo_check.get("checkStatus") or bpo_check.get("status") or "unavailable"
        bpo_reason = bpo_check.get("reason") or bpo_reason
        bpo_facts = bpo_check.get("facts") or {}
        bpo_details = {
            "proposalNumber": bpo_facts.get("proposalNumber"),
            "cpfMasked": bpo_facts.get("cpfMasked"),
            "situation": bpo_facts.get("situation"),
            "activity": bpo_facts.get("activity"),
            "documentCount": bpo_facts.get("documentCount"),
            "attentionPoints": len(bpo_check.get("attentionPoints") or []),
        }
    return [
        {"id": "azure-card", "status": "completed", "agent": "azure-devops-orchestrator", "capability": "read-card"},
        {
            "id": "restrictive-base",
            "status": restrictive_status,
            "agent": "sqlserver-data-analyzer",
            "capability": "run-readonly-query",
            "reason": restrictive_reason,
            **restrictive_details,
        },
        {
            "id": "cognito-user",
            "status": "ready_to_execute" if entities.get("cpfPresent") else "skipped",
            "agent": "future-cognito-analyzer",
            "capability": "read-user",
        },
        {
            "id": "onboarding-status",
            "status": "ready_to_execute" if has_customer_ref else "skipped",
            "agent": "postgres-data-analyzer",
            "capability": "run-readonly-query",
        },
        {
            "id": "proposal-status",
            "status": "ready_to_execute" if entities.get("proposalNumber") else "skipped",
            "agent": "postgres-data-analyzer",
            "capability": "run-readonly-query",
        },
        {
            "id": "bpo-proposal",
            "status": bpo_status,
            "agent": "bpo-analyser",
            "capability": "analyze-proposal" if entities.get("proposalNumber") else "analyze-cpf-proposals",
            "reason": bpo_reason,
            **bpo_details,
        },
        {
            "id": "customer-logs",
            "status": "ready_to_execute" if has_customer_ref or entities.get("requestId") else "skipped",
            "agent": "elasticsearch-log-analyzer",
            "capability": "search-log-events",
        },
    ]


def decide(
    entities: dict[str, Any],
    checks: list[dict[str, Any]],
    *,
    symptom_route: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not entities.get("cpfPresent") and not entities.get("proposalNumber") and not entities.get("requestId"):
        return {
            "status": "needs_more_info",
            "category": "insufficient_input",
            "confidence": 0.72,
            "summary": "Card nao contem CPF, proposta ou request id suficientes para executar o roteiro N1 completo.",
        }
    ready = [item for item in checks if item["status"] == "ready_to_execute"]
    restrictive = next((item for item in checks if item["id"] == "restrictive-base"), None)
    if restrictive and restrictive.get("status") == "hit":
        return {
            "status": "pending_n1_checks",
            "category": "restrictive_base_hit",
            "confidence": 0.76,
            "summary": "CPF encontrado na base restritiva. Ainda existem checks complementares antes da conclusao N1.",
        }
    return {
        "status": "pending_n1_checks",
        "category": symptom_route.get("domain") if symptom_route else "customer_operational_triage",
        "confidence": 0.68,
        "summary": (
            f"Entidades minimas encontradas. Rota {symptom_route.get('routeId') if symptom_route else '-'} "
            f"selecionada. {len(ready)} checks operacionais devem ser executados na sequencia do runbook."
        ),
    }


def recommended_action(decision: dict[str, Any]) -> dict[str, str]:
    if decision["status"] == "needs_more_info":
        return {
            "type": "request_info",
            "message": "Solicitar CPF, numero da proposta/contrato, horario do erro e evidencia do sintoma.",
        }
    return {
        "type": "continue_runbook",
        "message": "Executar checks de base restritiva, Cognito, onboarding, proposta e logs antes de concluir ou escalar.",
    }


def build_artifacts(
    card: dict[str, Any],
    entities: dict[str, Any],
    decision: dict[str, Any],
    checks: list[dict[str, Any]],
) -> dict[str, str]:
    pending = ", ".join(item["id"] for item in checks if item["status"] == "ready_to_execute") or "-"
    return {
        "internalComment": (
            f"Analise N1 iniciada para o card {card.get('id')}. "
            f"CPF={entities.get('cpfMasked') or '-'}, proposta={entities.get('proposalNumber') or '-'}. "
            f"Status: {decision['status']}. Checks pendentes: {pending}."
        ),
        "customerReply": recommended_action(decision)["message"],
        "n2Escalation": (
            f"Card {card.get('id')} - {card.get('title') or '-'} | "
            f"Decisao N1: {decision['status']} | Checks pendentes: {pending}."
        ),
    }


def pending_sources(checks: list[dict[str, Any]]) -> list[str]:
    return sorted({item["agent"] for item in checks if item["status"] == "ready_to_execute"})


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split())


def value_or_dash(value: Any) -> str:
    text = clean_text(value)
    return text if text else "-"


def truncate(value: str, limit: int = 600) -> str:
    text = clean_text(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."
