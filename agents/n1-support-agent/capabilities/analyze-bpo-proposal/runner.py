#!/usr/bin/env python3
"""Runner for n1-support-agent/analyze-bpo-proposal."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys
from typing import Any

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    load_fixture,
    mask_cpf,
    print_error,
    run_ai_devkit_json,
    truncate,
    value_or_dash,
    write_output,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run n1-support-agent/analyze-bpo-proposal")
    parser.add_argument("--cpf")
    parser.add_argument("--proposal-number")
    parser.add_argument("--document-type")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    try:
        payload = analyze(args)
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render(payload)
        write_output(content, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def analyze(args: argparse.Namespace) -> dict[str, Any]:
    fixture = load_fixture(args.fixture) if args.fixture else None
    direct_fixture = extract_bpo_fixture(fixture)
    proposal_number = args.proposal_number or extract_proposal_number(fixture)
    cpf = args.cpf or extract_cpf(fixture)

    if direct_fixture:
        return normalize_bpo_payload(
            direct_fixture,
            source_query="fixture",
            proposal_number=proposal_number,
            cpf=cpf,
        )

    if fixture:
        if proposal_number or cpf:
            return unavailable_payload(
                proposal_number=proposal_number,
                cpf=cpf,
                reason="BPO fixture was not provided",
            )
        return base_payload(status="skipped", proposal_number=None, cpf=None, reason="CPF or proposal number was not provided")

    if proposal_number:
        try:
            bpo_payload = run_ai_devkit_json(
                [
                    "run",
                    "bpo-analyser",
                    "analyze-proposal",
                    "--proposal-number",
                    proposal_number,
                    "--format",
                    "json",
                    *(["--document-type", args.document_type] if args.document_type else []),
                ]
            )
            return normalize_bpo_payload(
                bpo_payload,
                source_query="proposal",
                proposal_number=proposal_number,
                cpf=cpf,
            )
        except Exception as exc:
            return unavailable_payload(proposal_number=proposal_number, cpf=cpf, reason=truncate(str(exc), 240))

    if cpf:
        try:
            bpo_payload = run_ai_devkit_json(
                [
                    "run",
                    "bpo-analyser",
                    "analyze-cpf-proposals",
                    "--cpf",
                    cpf,
                    "--format",
                    "json",
                ]
            )
            return normalize_bpo_payload(
                bpo_payload,
                source_query="cpf",
                proposal_number=None,
                cpf=cpf,
            )
        except Exception as exc:
            return unavailable_payload(proposal_number=None, cpf=cpf, reason=truncate(str(exc), 240))

    return base_payload(status="skipped", proposal_number=None, cpf=None, reason="CPF or proposal number was not provided")


def extract_bpo_fixture(fixture: dict[str, Any] | None) -> dict[str, Any] | None:
    if not fixture:
        return None
    for key in ("bpo", "bpo_proposal", "bpoProposal"):
        value = fixture.get(key)
        if isinstance(value, dict):
            return value
    if "proposal" in fixture or "proposals" in fixture or "facts" in fixture:
        return fixture
    return None


def normalize_bpo_payload(
    payload: dict[str, Any],
    *,
    source_query: str,
    proposal_number: str | None,
    cpf: str | None,
) -> dict[str, Any]:
    facts = payload.get("facts") or {}
    proposal = payload.get("proposal") or facts.get("latest_integrated_or_approved") or payload.get("selected") or {}
    documents = payload.get("documents") or {}
    inferences = payload.get("inferences") or {}
    selected_proposal = proposal if isinstance(proposal, dict) else {}
    normalized_proposal = str(
        proposal_number
        or facts.get("proposal_number")
        or selected_proposal.get("proposal_number")
        or ""
    ) or None
    normalized_cpf = cpf or selected_proposal.get("cpf") or (selected_proposal.get("customer") or {}).get("cpf") or payload.get("cpf")
    status = classify_status(payload)
    result = base_payload(
        status=status,
        proposal_number=normalized_proposal,
        cpf=normalized_cpf,
        reason=reason_for_status(status, selected_proposal, facts),
    )
    result.update(
        {
            "sourceQuery": source_query,
            "facts": {
                "proposalNumber": normalized_proposal,
                "cpfMasked": mask_cpf(normalized_cpf) if normalized_cpf else None,
                "situation": facts.get("situation") or selected_proposal.get("situation"),
                "activity": facts.get("activity") or selected_proposal.get("activity"),
                "processingStatus": (selected_proposal.get("processing_status") or {}).get("status"),
                "processingError": (selected_proposal.get("processing_status") or {}).get("error_message"),
                "situationDate": selected_proposal.get("situation_date"),
                "observationCount": facts.get("observation_count") or len(selected_proposal.get("observations") or []),
                "documentCount": facts.get("document_count") if "document_count" in facts else documents.get("count"),
                "documentTypes": facts.get("document_types") or document_types(documents),
                "proposalCount": facts.get("total") or payload.get("count"),
                "eligibleCount": facts.get("eligible_count"),
                "underAnalysisCount": facts.get("under_analysis_count"),
                "rejectedCount": facts.get("rejected_count"),
            },
            "attentionPoints": inferences.get("attention_points") or [],
            "hasBlockingSignals": bool(inferences.get("has_blocking_signals")),
            "rawEvidenceSummary": summarize_evidence(selected_proposal, documents),
        }
    )
    return result


def base_payload(
    *,
    status: str,
    proposal_number: str | None,
    cpf: str | None,
    reason: str,
) -> dict[str, Any]:
    return {
        "capability": "analyze-bpo-proposal",
        "status": "completed" if status in {"found", "not_found", "pending", "rejected", "skipped"} else "unavailable",
        "checkStatus": status,
        "reason": reason,
        "agent": "n1-support-agent",
        "orchestratedAgent": "bpo-analyser",
        "orchestratedCapability": "analyze-proposal" if proposal_number else "analyze-cpf-proposals",
        "facts": {
            "proposalNumber": proposal_number,
            "cpfMasked": mask_cpf(cpf) if cpf else None,
        },
        "attentionPoints": [],
        "hasBlockingSignals": False,
        "rawEvidenceSummary": [],
        "errors": [],
    }


def unavailable_payload(*, proposal_number: str | None, cpf: str | None, reason: str) -> dict[str, Any]:
    payload = base_payload(status="unavailable", proposal_number=proposal_number, cpf=cpf, reason=reason)
    payload["errors"] = [{"error": reason}]
    return payload


def classify_status(payload: dict[str, Any]) -> str:
    facts = payload.get("facts") or {}
    proposal = payload.get("proposal") or payload.get("selected") or facts.get("latest_integrated_or_approved") or {}
    proposals = payload.get("proposals") or []
    if not proposal and not proposals and not facts.get("total"):
        return "not_found"
    text = normalize(" ".join(str(value or "") for value in [
        facts.get("situation"),
        facts.get("activity"),
        proposal.get("situation") if isinstance(proposal, dict) else "",
        proposal.get("activity") if isinstance(proposal, dict) else "",
    ]))
    if any(token in text for token in ("reprov", "recus", "negad", "cancel", "rejeit")):
        return "rejected"
    if any(token in text for token in ("pend", "analise", "andamento", "formaliz", "aguard")):
        return "pending"
    if facts.get("under_analysis_count"):
        return "pending"
    return "found"


def reason_for_status(status: str, proposal: dict[str, Any], facts: dict[str, Any]) -> str:
    if status == "not_found":
        return "No BPO proposal evidence was found"
    if status == "pending":
        return "BPO proposal has pending or under-analysis signals"
    if status == "rejected":
        return "BPO proposal has rejected/cancelled signals"
    if status == "found":
        return "BPO proposal evidence was found"
    return facts.get("reason") or proposal.get("reason") or "-"


def summarize_evidence(proposal: dict[str, Any], documents: dict[str, Any]) -> list[str]:
    summary = []
    if proposal.get("situation"):
        summary.append(f"situation={proposal.get('situation')}")
    if proposal.get("activity"):
        summary.append(f"activity={proposal.get('activity')}")
    if documents:
        summary.append(f"documents={documents.get('count') if documents.get('count') is not None else len(documents.get('files') or [])}")
    return summary


def document_types(documents: dict[str, Any]) -> list[str]:
    return sorted(
        {
            str(item.get("document_type"))
            for item in documents.get("files") or []
            if item.get("document_type")
        }
    )


def extract_proposal_number(fixture: dict[str, Any] | None) -> str | None:
    if not fixture:
        return None
    text = fixture_text(fixture)
    match = re.search(r"(?i)\b(?:proposta|proposal)\D{0,20}(\d{4,})\b", text)
    return match.group(1) if match else None


def extract_cpf(fixture: dict[str, Any] | None) -> str | None:
    if not fixture:
        return None
    text = fixture_text(fixture)
    match = re.search(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", text)
    return match.group(0) if match else None


def fixture_text(fixture: dict[str, Any]) -> str:
    work_item = fixture.get("work_item") or fixture.get("card") or {}
    comments = fixture.get("comments") or {}
    comment_items = comments.get("comments", []) if isinstance(comments, dict) else comments or []
    return "\n".join(
        [
            str(work_item.get("title") or ""),
            str(work_item.get("description") or ""),
            json.dumps(extract_bpo_fixture(fixture) or {}, ensure_ascii=False),
            *[str(item.get("text") or item.get("body") or "") for item in comment_items],
        ]
    )


def normalize(value: str) -> str:
    return " ".join(str(value or "").lower().split())


def render(payload: dict[str, Any]) -> str:
    facts = payload.get("facts") or {}
    lines = [
        "# N1 BPO Proposal Check",
        "",
        f"- Status: {payload.get('checkStatus')}",
        f"- Reason: {value_or_dash(payload.get('reason'))}",
        f"- Proposal: {value_or_dash(facts.get('proposalNumber'))}",
        f"- CPF: {value_or_dash(facts.get('cpfMasked'))}",
        f"- Situation: {value_or_dash(facts.get('situation'))}",
        f"- Activity: {value_or_dash(facts.get('activity'))}",
        f"- Documents: {value_or_dash(facts.get('documentCount'))}",
        "",
        "## Attention Points",
        "",
    ]
    attention = payload.get("attentionPoints") or []
    lines.extend(f"- {item}" for item in attention) if attention else lines.append("- No attention points.")
    lines.extend(["", "## Contract", "", "```json", json.dumps(payload, ensure_ascii=False, indent=2), "```"])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
