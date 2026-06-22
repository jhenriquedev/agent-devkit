#!/usr/bin/env python3
"""MeuCashCard knowledge routing helpers for N1 Support Agent."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
AGENT_DIR = ROOT / "agents" / "n1-support-agent"
MCC_KNOWLEDGE_DIR = AGENT_DIR / "knowledge" / "domains" / "meucashcard"


def route_customer_symptom(text: str, entities: dict[str, Any] | None = None) -> dict[str, Any]:
    routing = load_json(MCC_KNOWLEDGE_DIR / "symptom-routing.json")
    routes = routing.get("routes") or []
    normalized_text = normalize(text)
    scored = [score_route(route, normalized_text) for route in routes]
    scored.sort(key=lambda item: (-item["score"], item["route"].get("id", "")))
    best = scored[0] if scored and scored[0]["score"] > 0 else {"route": routing["defaultRoute"], "score": 0, "matchedAliases": []}
    route = best["route"]
    domain = route.get("domain") or "unknown"
    knowledge_files = route.get("knowledgeFiles") or []
    business_rules = load_business_rules(knowledge_files)
    contract = load_json(MCC_KNOWLEDGE_DIR / "contracts" / "n1-support-triage-contract.json")
    playbook = load_json(MCC_KNOWLEDGE_DIR / "playbooks" / "global-support-diagnostics.json")
    return {
        "routeId": route.get("id"),
        "domain": domain,
        "label": route.get("label"),
        "confidence": route_confidence(best["score"]),
        "matchedAliases": best["matchedAliases"],
        "knowledgeFiles": knowledge_files,
        "evidencePlanIds": route.get("evidencePlanIds") or [],
        "minimumChecks": route.get("minimumChecks") or [],
        "validConclusions": route.get("validConclusions") or [],
        "insufficientIfMissing": route.get("insufficientIfMissing") or [],
        "businessRules": select_relevant_rules(business_rules, normalized_text, domain),
        "qualityGate": contract.get("qualityGate") or {},
        "operatingPrinciples": playbook.get("operatingPrinciples") or [],
        "diagnosticGaps": build_initial_gaps(route, entities or {}),
    }


def build_evidence_ledger(
    *,
    checks: list[dict[str, Any]],
    symptom_route: dict[str, Any],
) -> list[dict[str, Any]]:
    ledger = []
    for check in checks:
        status = check.get("status")
        ledger_status = "succeeded" if status in {"completed", "clear", "hit", "found", "not_found", "pending", "rejected"} else "skipped" if status == "skipped" else "pending"
        ledger.append(
            {
                "sourceType": check_source_type(check),
                "sourceKey": check.get("agent"),
                "queryKey": check.get("capability"),
                "title": check.get("id"),
                "status": ledger_status,
                "rowCount": check.get("findings", 0),
                "summary": check_summary(check),
                "relevantFindings": relevant_findings(check),
                "metadata": {
                    "routeId": symptom_route.get("routeId"),
                    "domain": symptom_route.get("domain"),
                },
                "error": None,
            }
        )
    return ledger


def evaluate_quality_gate(
    *,
    entities: dict[str, Any],
    checks: list[dict[str, Any]],
    symptom_route: dict[str, Any],
) -> dict[str, Any]:
    failures = []
    pending = [item["id"] for item in checks if item.get("status") == "ready_to_execute"]
    unavailable = [item["id"] for item in checks if item.get("status") == "unavailable"]
    if not (entities.get("cpfPresent") or entities.get("proposalNumber") or entities.get("requestId")):
        failures.append("card possui poucos identificadores objetivos")
    if not symptom_route.get("routeId"):
        failures.append("routeId nao foi selecionado")
    if pending:
        failures.append("minimumChecks ainda pendentes: " + ", ".join(pending))
    if unavailable:
        failures.append("minimumChecks indisponiveis: " + ", ".join(unavailable))
    return {
        "understandableByN2": bool(symptom_route.get("routeId")),
        "understandableByN3": len(failures) == 0,
        "understandableByDev": len(failures) == 0,
        "hasOpenQuestions": bool(failures),
        "delegatesUnderstanding": False,
        "passed": len(failures) == 0,
        "failures": failures,
        "mustAnswer": load_json(MCC_KNOWLEDGE_DIR / "playbooks" / "global-support-diagnostics.json").get("mustAnswer") or [],
    }


def build_diagnostic_gaps(
    *,
    checks: list[dict[str, Any]],
    symptom_route: dict[str, Any],
) -> list[dict[str, str]]:
    gaps = []
    for check in checks:
        if check.get("status") == "ready_to_execute":
            gaps.append(
                {
                    "id": f"pending-{check['id']}",
                    "source": check.get("agent") or "-",
                    "reason": check.get("reason") or "Check operacional ainda nao executado.",
                }
            )
        if check.get("status") == "unavailable":
            gaps.append(
                {
                    "id": f"unavailable-{check['id']}",
                    "source": check.get("source") or check.get("agent") or "-",
                    "reason": check.get("reason") or "Ferramenta necessaria nao esta disponivel para este check.",
                }
            )
    if not symptom_route.get("matchedAliases") and symptom_route.get("domain") == "unknown":
        gaps.append(
            {
                "id": "weak-symptom-route",
                "source": "meucashcard-symptom-routing",
                "reason": "Sintoma nao casou com rota especifica do knowledge.",
            }
        )
    return gaps


def score_route(route: dict[str, Any], normalized_text: str) -> dict[str, Any]:
    matched = []
    score = 0
    for alias in route.get("aliases") or []:
        normalized_alias = normalize(alias)
        if not normalized_alias:
            continue
        if normalized_alias in normalized_text:
            matched.append(alias)
            score += 3
            continue
        tokens = [token for token in normalized_alias.split() if len(token) > 2]
        if tokens and all(token in normalized_text for token in tokens):
            matched.append(alias)
            score += 1
    domain = route.get("domain")
    if domain and domain in normalized_text:
        score += 1
    return {"route": route, "score": score, "matchedAliases": matched}


def load_business_rules(knowledge_files: list[str]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for ref in knowledge_files:
        if not ref.startswith("rules/"):
            continue
        payload = load_json(MCC_KNOWLEDGE_DIR / ref)
        for rule in payload.get("rules") or []:
            rules.append({**rule, "knowledgeFile": ref})
    return rules


def select_relevant_rules(
    rules: list[dict[str, Any]],
    normalized_text: str,
    domain: str,
    limit: int = 8,
) -> list[dict[str, Any]]:
    scored = []
    for rule in rules:
        searchable = normalize(" ".join(str(rule.get(key, "")) for key in ("id", "category", "rule", "supportImpact")))
        score = sum(1 for token in set(normalized_text.split()) if len(token) > 3 and token in searchable)
        if domain and domain in searchable:
            score += 1
        scored.append((score, rule))
    scored.sort(key=lambda item: (-item[0], item[1].get("id", "")))
    selected = [rule for score, rule in scored if score > 0][:limit]
    if selected:
        return selected
    return [rule for _, rule in scored[: min(limit, len(scored))]]


def build_initial_gaps(route: dict[str, Any], entities: dict[str, Any]) -> list[dict[str, str]]:
    gaps = []
    if not entities.get("cpfPresent") and route.get("domain") not in {"unknown", None}:
        gaps.append(
            {
                "id": "missing-cpf",
                "source": "card",
                "reason": "CPF nao foi identificado; checks por cliente ficam limitados.",
            }
        )
    return gaps


def check_source_type(check: dict[str, Any]) -> str:
    agent = str(check.get("agent") or "")
    if "azure" in agent:
        return "ticket"
    if "bpo" in agent:
        return "external_system"
    if "sqlserver" in agent or "postgres" in agent:
        return "database"
    if "cloudwatch" in agent or "elastic" in agent:
        return "log"
    return "tool"


def check_summary(check: dict[str, Any]) -> str:
    status = check.get("status")
    reason = check.get("reason")
    parts = [f"{check.get('id')} status={status}"]
    if reason:
        parts.append(str(reason))
    return "; ".join(parts)


def relevant_findings(check: dict[str, Any]) -> list[str]:
    findings = []
    if check.get("cpfMasked"):
        findings.append(f"CPF {check['cpfMasked']}")
    if check.get("proposalNumber"):
        findings.append(f"proposal {check['proposalNumber']}")
    if check.get("documentCount") is not None:
        findings.append(f"{check.get('documentCount')} document(s)")
    if "findings" in check:
        findings.append(f"{check.get('findings')} finding(s)")
    if "candidatesChecked" in check:
        findings.append(f"{check.get('candidatesChecked')} candidate(s) checked")
    return findings


def route_confidence(score: int) -> float:
    if score >= 6:
        return 0.86
    if score >= 3:
        return 0.72
    if score >= 1:
        return 0.58
    return 0.32


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()
