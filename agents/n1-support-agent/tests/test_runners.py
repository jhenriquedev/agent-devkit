#!/usr/bin/env python3
"""Smoke tests for N1 Support Agent runners through ai-devkit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


class N1SupportAgentRunnerTest(unittest.TestCase):
    def test_execute_card_runbook_from_fixture(self) -> None:
        fixture = {
            "work_item": {
                "id": 7710,
                "work_item_type": "Issue",
                "title": "Cliente 123.456.789-09 nao conclui onboarding proposta 987654",
                "state": "New",
                "board_column": "A Iniciar",
                "assigned_to": "n1@example.com",
                "tags": ["topdesk"],
                "description": "Erro no onboarding para CPF 12345678909. Request 123e4567-e89b-12d3-a456-426614174000.",
                "created_date": "2026-06-21T10:00:00Z",
                "changed_date": "2026-06-21T11:00:00Z",
                "relations": [
                    {"rel": "AttachedFile", "attributes": {"name": "erro.png"}},
                ],
            },
            "comments": {
                "comments": [
                    {
                        "author": "Analista",
                        "created_at": "2026-06-21T11:20:00Z",
                        "text": "Chamado TOPdesk T2606-1234 relacionado.",
                    }
                ]
            },
            "restrictive_base": {
                "checkStatus": "clear",
                "findings": [],
                "candidatesChecked": [
                    {"sourceTable": "dbo.RestrictiveCustomer", "cpfColumn": "cpf"}
                ],
            },
            "bpo": {
                "proposal": {
                    "proposal_number": "987654",
                    "processing_status": {"status": True, "error_message": ""},
                    "situation": "Pendente",
                    "activity": "Analise de documentos",
                    "situation_date": "2026-06-21T09:30:00",
                    "customer_name": "Cliente Teste",
                    "cpf": "12345678909",
                    "product_name": "Cartao Beneficio",
                    "proposal_type": "Saque",
                    "observations": [{"date": "2026-06-21", "text": "Aguardando documento"}],
                },
                "documents": {
                    "proposal_number": "987654",
                    "requested_document_type": "Nao_Definido",
                    "processing_status": {"status": True, "error_message": ""},
                    "count": 1,
                    "files": [
                        {
                            "proposal_number": 987654,
                            "file_name": "ccb.pdf",
                            "document_type": "CCB_Negociavel",
                            "extension_file_type": "PDF",
                            "size": 2048,
                            "has_file_base64": True,
                        }
                    ],
                },
                "facts": {
                    "proposal_number": "987654",
                    "situation": "Pendente",
                    "activity": "Analise de documentos",
                    "observation_count": 1,
                    "document_count": 1,
                    "document_types": ["CCB_Negociavel"],
                },
                "inferences": {
                    "attention_points": ["Proposta pendente na BPO por documento."],
                    "has_blocking_signals": True,
                },
            },
        }

        result = run_capability(
            "execute-n1-card-runbook",
            fixture,
            [
                "--project",
                "Sustentacao",
                "--card",
                "7710",
                "--target-column",
                "Em Analise N1",
            ],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# N1 Card Runbook", result.stdout)
        self.assertIn("123.***.***-09", result.stdout)
        self.assertIn("add-analysis-tag", result.stdout)
        self.assertIn("move-card", result.stdout)
        self.assertIn("restrictive-base: clear", result.stdout)
        self.assertIn("bpo-proposal: pending", result.stdout)
        self.assertIn('"status": "pending_n1_checks"', result.stdout)

    def test_execute_card_runbook_json_contract_from_fixture(self) -> None:
        fixture = {
            "work_item": {
                "id": 42,
                "title": "Sem dados suficientes",
                "state": "New",
                "board_column": "A Iniciar",
                "tags": [],
                "description": "Usuario informou erro generico.",
            },
            "comments": {"comments": []},
        }

        result = run_capability(
            "execute-n1-card-runbook",
            fixture,
            ["--project", "Sustentacao", "--card", "42", "--format", "json"],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["runbook"], "n1-card-operational-triage")
        self.assertEqual(payload["decision"]["status"], "needs_more_info")

    def test_execute_card_runbook_enriches_contract_with_mcc_knowledge(self) -> None:
        fixture = {
            "work_item": {
                "id": 7711,
                "title": "Cliente 123.456.789-09 nao consegue concluir cadastro",
                "state": "New",
                "board_column": "A Iniciar",
                "tags": ["topdesk"],
                "description": (
                    "Cliente relata onboarding travado na etapa de documentos para CPF 12345678909. "
                    "Convenio INSS, matricula 998877, erro ao avancar etapa."
                ),
            },
            "comments": {"comments": []},
            "restrictive_base": {
                "checkStatus": "clear",
                "findings": [],
                "candidatesChecked": [
                    {"sourceTable": "dbo.restrictive", "cpfColumn": "document"}
                ],
            },
        }

        result = run_capability(
            "execute-n1-card-runbook",
            fixture,
            ["--project", "Sustentacao", "--card", "7711", "--format", "json"],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["symptomRoute"]["routeId"], "symptom.onboarding_stuck_or_step_error")
        self.assertEqual(payload["symptomRoute"]["domain"], "onboarding")
        self.assertIn("businessRulesApplied", payload)
        rule_ids = {rule["id"] for rule in payload["businessRulesApplied"]}
        self.assertIn("onboarding.start.restrictive_base_blocks", rule_ids)
        self.assertIn("qualityGate", payload)
        self.assertIn("evidenceLedger", payload)
        self.assertIn("diagnosticGaps", payload)

    def test_execute_card_runbook_marks_unavailable_checks_as_open_quality_gate(self) -> None:
        fixture = {
            "work_item": {
                "id": 7713,
                "title": "Cliente 123.456.789-09 nao consegue concluir cadastro proposta 987654",
                "state": "New",
                "board_column": "A Iniciar",
                "tags": [],
                "description": "Onboarding travado para CPF 12345678909.",
            },
            "comments": {"comments": []},
            "restrictive_base": {
                "checkStatus": "clear",
                "findings": [],
                "candidatesChecked": [],
            },
        }

        result = run_capability(
            "execute-n1-card-runbook",
            fixture,
            ["--project", "Sustentacao", "--card", "7713", "--format", "json"],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["qualityGate"]["passed"])
        self.assertTrue(payload["qualityGate"]["hasOpenQuestions"])
        self.assertTrue(any("minimumChecks indisponiveis" in item for item in payload["qualityGate"]["failures"]))
        self.assertIn("checks indisponiveis", payload["decision"]["summary"])

    def test_analyze_bpo_proposal_from_fixture_maps_pending_proposal(self) -> None:
        fixture = {
            "proposal": {
                "proposal_number": "987654",
                "processing_status": {"status": True, "error_message": ""},
                "situation": "Pendente",
                "activity": "Analise de documentos",
                "situation_date": "2026-06-21T09:30:00",
                "customer_name": "Cliente Teste",
                "cpf": "12345678909",
                "product_name": "Cartao Beneficio",
                "proposal_type": "Saque",
                "observations": [{"date": "2026-06-21", "text": "Aguardando documento"}],
            },
            "documents": {
                "proposal_number": "987654",
                "requested_document_type": "Nao_Definido",
                "processing_status": {"status": True, "error_message": ""},
                "count": 1,
                "files": [
                    {
                        "proposal_number": 987654,
                        "file_name": "ccb.pdf",
                        "document_type": "CCB_Negociavel",
                        "extension_file_type": "PDF",
                        "size": 2048,
                        "has_file_base64": True,
                    }
                ],
            },
            "facts": {
                "proposal_number": "987654",
                "situation": "Pendente",
                "activity": "Analise de documentos",
                "observation_count": 1,
                "document_count": 1,
                "document_types": ["CCB_Negociavel"],
            },
            "inferences": {
                "attention_points": ["Proposta pendente na BPO por documento."],
                "has_blocking_signals": True,
            },
        }

        result = run_capability(
            "analyze-bpo-proposal",
            fixture,
            ["--proposal-number", "987654", "--format", "json"],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["checkStatus"], "pending")
        self.assertEqual(payload["facts"]["proposalNumber"], "987654")
        self.assertEqual(payload["facts"]["documentCount"], 1)
        self.assertEqual(payload["facts"]["cpfMasked"], "123.***.***-09")
        self.assertNotIn("12345678909", result.stdout)

    def test_execute_card_runbook_includes_bpo_evidence_from_fixture(self) -> None:
        fixture = {
            "work_item": {
                "id": 7712,
                "title": "Cliente 123.456.789-09 com proposta 987654 em formalizacao",
                "state": "New",
                "board_column": "A Iniciar",
                "tags": [],
                "description": "Cliente informa que a CCB da proposta 987654 nao aparece.",
            },
            "comments": {"comments": []},
            "bpo": {
                "proposal": {
                    "proposal_number": "987654",
                    "processing_status": {"status": True, "error_message": ""},
                    "situation": "Pendente",
                    "activity": "Formalizacao",
                    "cpf": "12345678909",
                    "observations": [],
                },
                "documents": {
                    "proposal_number": "987654",
                    "count": 0,
                    "files": [],
                },
                "facts": {
                    "proposal_number": "987654",
                    "situation": "Pendente",
                    "activity": "Formalizacao",
                    "observation_count": 0,
                    "document_count": 0,
                    "document_types": [],
                },
                "inferences": {
                    "attention_points": ["Documento CCB ausente na BPO."],
                    "has_blocking_signals": True,
                },
            },
        }

        result = run_capability(
            "execute-n1-card-runbook",
            fixture,
            ["--project", "Sustentacao", "--card", "7712", "--format", "json"],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        bpo_check = next(item for item in payload["checks"] if item["id"] == "bpo-proposal")
        self.assertEqual(bpo_check["status"], "pending")
        self.assertEqual(bpo_check["agent"], "bpo-analyser")
        self.assertIn("bpo-analyser", payload["audit"]["orchestratedAgents"])
        self.assertIn("bpo", payload["audit"]["dataSources"])
        self.assertTrue(any(item["title"] == "bpo-proposal" for item in payload["evidenceLedger"]))

    def test_analyze_restrictive_base_from_fixture_masks_cpf_and_reports_hit(self) -> None:
        fixture = {
            "cpf": "123.456.789-09",
            "checkStatus": "hit",
            "findings": [
                {
                    "sourceTable": "dbo.RestrictiveCustomer",
                    "cpfColumn": "cpf",
                    "rowCount": 1,
                    "rows": [
                        {
                            "cpf": "12345678909",
                            "reason": "Bloqueio manual",
                            "active": True,
                        }
                    ],
                }
            ],
        }

        result = run_capability(
            "analyze-restrictive-base",
            fixture,
            ["--cpf", "123.456.789-09", "--format", "json"],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["checkStatus"], "hit")
        self.assertEqual(payload["cpfMasked"], "123.***.***-09")
        self.assertEqual(payload["findings"][0]["rows"][0]["cpf"], "123.***.***-09")

    def test_route_customer_symptom_from_fixture_selects_onboarding_route(self) -> None:
        fixture = {
            "text": (
                "Cliente 123.456.789-09 nao consegue concluir cadastro. "
                "Onboarding travado em documentos, convenio INSS, matricula 998877."
            )
        }

        result = run_capability(
            "route-customer-symptom",
            fixture,
            ["--format", "json"],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["routeId"], "symptom.onboarding_stuck_or_step_error")
        self.assertEqual(payload["domain"], "onboarding")
        self.assertIn("rules/onboarding-rules.json", payload["knowledgeFiles"])
        self.assertIn("Consultar Onboarding por CPF e validar se existe finalizado ou em andamento.", payload["minimumChecks"])
        rule_ids = {rule["id"] for rule in payload["businessRules"]}
        self.assertIn("onboarding.start.restrictive_base_blocks", rule_ids)

    def test_extract_card_entities_masks_cpf_and_finds_operational_ids(self) -> None:
        fixture = {
            "text": (
                "Cliente CPF 12345678909 com proposta 987654, contrato ABCD-1234, "
                "TOPdesk T2606-1234 e erro request 123e4567-e89b-12d3-a456-426614174000."
            )
        }

        result = run_capability("extract-card-entities", fixture, ["--format", "json"])

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["capability"], "extract-card-entities")
        self.assertEqual(payload["entities"]["cpfMasked"], "123.***.***-09")
        self.assertEqual(payload["entities"]["proposalNumber"], "987654")
        self.assertEqual(payload["entities"]["contractNumber"], "ABCD-1234")
        self.assertEqual(payload["entities"]["topdeskTicket"], "T2606-1234")
        self.assertNotIn("12345678909", result.stdout)
        self.assertNotEqual(payload["status"], "contract_ready")

    def test_decide_n1_outcome_applies_domain_rules(self) -> None:
        fixture = {
            "entities": {"cpfPresent": True, "cpfMasked": "123.***.***-09", "proposalNumber": "987654"},
            "symptomRoute": {
                "routeId": "symptom.onboarding_stuck_or_step_error",
                "domain": "onboarding",
                "businessRules": [
                    {
                        "id": "onboarding.start.restrictive_base_blocks",
                        "supportImpact": "Restritiva clear/hit/unavailable muda o diagnostico.",
                    }
                ],
            },
            "checks": [
                {"id": "azure-card", "status": "completed", "agent": "azure-devops-orchestrator"},
                {"id": "restrictive-base", "status": "clear", "agent": "sqlserver-data-analyzer"},
                {"id": "onboarding-status", "status": "unavailable", "agent": "n1-support-agent"},
            ],
        }

        result = run_capability("decide-n1-outcome", fixture, ["--format", "json"])

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["capability"], "decide-n1-outcome")
        self.assertEqual(payload["decision"]["status"], "pending_n1_checks")
        rule_ids = {rule["id"] for rule in payload["businessRulesApplied"]}
        self.assertIn("onboarding.start.restrictive_base_blocks", rule_ids)
        self.assertIn("qualityGate", payload)
        self.assertNotEqual(payload["status"], "contract_ready")

    def test_generate_n1_artifacts_uses_masked_entities(self) -> None:
        fixture = {
            "card": {"id": 7710, "title": "Cliente nao conclui onboarding"},
            "entities": {"cpfMasked": "123.***.***-09", "proposalNumber": "987654"},
            "decision": {
                "status": "pending_n1_checks",
                "category": "onboarding",
                "confidence": 0.68,
                "summary": "Continuar checks N1.",
            },
            "checks": [
                {"id": "cognito-user", "status": "unavailable"},
                {"id": "onboarding-status", "status": "unavailable"},
            ],
        }

        result = run_capability("generate-n1-artifacts", fixture, ["--format", "json"])

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        artifacts = payload["artifacts"]
        self.assertIn("internalComment", artifacts)
        self.assertIn("customerReply", artifacts)
        self.assertIn("n2Escalation", artifacts)
        self.assertIn("123.***.***-09", artifacts["internalComment"])
        self.assertNotIn("12345678909", result.stdout)
        self.assertNotEqual(payload["status"], "contract_ready")

    def test_update_azure_card_plans_dry_run_by_default(self) -> None:
        fixture = {
            "work_item": {
                "id": 7710,
                "title": "Cliente nao conclui onboarding",
                "state": "New",
                "board_column": "A Iniciar",
                "tags": [],
            }
        }

        result = run_capability(
            "update-azure-card",
            fixture,
            [
                "--project",
                "Sustentacao",
                "--card",
                "7710",
                "--tag",
                "Analise N1",
                "--target-column",
                "Em Analise N1",
                "--current-state",
                "New",
                "--format",
                "json",
            ],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["capability"], "update-azure-card")
        self.assertEqual([action["mode"] for action in payload["azureActions"]], ["dry_run", "dry_run"])
        self.assertNotEqual(payload["status"], "contract_ready")

    def test_analyze_cognito_user_reports_unavailable_diagnostic_gap(self) -> None:
        result = run_capability(
            "analyze-cognito-user",
            {"cpf": "12345678909"},
            ["--cpf", "12345678909", "--format", "json"],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["capability"], "analyze-cognito-user")
        self.assertEqual(payload["checkStatus"], "unavailable")
        self.assertEqual(payload["diagnosticGaps"][0]["source"], "cognito")
        self.assertEqual(payload["facts"]["cpfMasked"], "123.***.***-09")
        self.assertNotIn("future-" + "cognito-analyzer", result.stdout)
        self.assertNotIn("12345678909", result.stdout)


def run_capability(capability: str, fixture: dict, extra_args: list[str]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = Path(tmpdir) / "fixture.json"
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(CLI),
                "run",
                "n1-support-agent",
                capability,
                *extra_args,
                "--fixture",
                str(fixture_path),
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


if __name__ == "__main__":
    unittest.main()
