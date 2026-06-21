#!/usr/bin/env python3
"""Smoke tests for N2 Support Agent runners through ai-devkit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


class N2SupportAgentRunnerTest(unittest.TestCase):
    def test_generate_patch_plan_writes_requested_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "patch_plan.md"
            codebase = create_codebase(Path(tmpdir))
            fixture = {
                "supportContext": {
                    "symptom": "Cliente nao consegue concluir onboarding por documento pendente.",
                    "rootCauseHint": "backend should validate document status before advancing onboarding",
                    "evidence": ["BPO retornou proposta pendente em documentos."],
                }
            }

            result = run_capability(
                "generate-patch-plan",
                fixture,
                [
                    "--codebase-path",
                    str(codebase),
                    "--output",
                    str(output),
                    "--format",
                    "json",
                ],
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(output.exists())
            self.assertEqual(payload["patchPlan"]["path"], str(output))
            self.assertEqual(payload["patchPlan"]["deliveryMode"], "local_path")
            content = output.read_text(encoding="utf-8")
            self.assertIn("# Patch Plan", content)
            self.assertIn("## Plano TDD", content)
            self.assertIn("## Criterios de aceite finais", content)
            self.assertIn("src/onboarding_service.py", content)
            self.assertNotIn("12345678901", content)

    def test_execute_n2_investigation_generates_root_cause_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "patch_plan.md"
            codebase = create_codebase(Path(tmpdir))
            fixture = {
                "work_item": {
                    "id": 8801,
                    "title": "Cliente 123.456.789-09 nao avanca onboarding proposta 987654",
                    "state": "Em Analise N2",
                    "board_column": "N2",
                    "tags": ["Analise N1"],
                    "description": "Erro ao avancar etapa de documentos no onboarding.",
                },
                "comments": {"comments": []},
                "n1_contract": {
                    "runbook": "n1-card-operational-triage",
                    "entities": {
                        "cpfMasked": "123.***.***-09",
                        "proposalNumber": "987654",
                    },
                    "checks": [
                        {"id": "bpo-proposal", "status": "pending", "reason": "BPO proposal has pending document signals"},
                        {"id": "onboarding-status", "status": "ready_to_execute"},
                    ],
                    "diagnosticGaps": [],
                    "decision": {"status": "pending_n1_checks", "category": "onboarding"},
                },
            }

            result = run_capability(
                "execute-n2-investigation",
                fixture,
                [
                    "--project",
                    "Sustentacao",
                    "--card",
                    "8801",
                    "--codebase-path",
                    str(codebase),
                    "--output",
                    str(output),
                    "--format",
                    "json",
                ],
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["runbook"], "n2-root-cause-investigation")
            self.assertTrue(payload["supportContext"]["azureCardLoaded"])
            self.assertTrue(payload["supportContext"]["n1ContractLoaded"])
            self.assertEqual(payload["rootCause"]["category"], "backend_bug")
            self.assertTrue(payload["codeAnalysis"]["filesInspected"][0].startswith("src/"))
            self.assertTrue(output.exists())
            self.assertEqual(payload["patchPlan"]["path"], str(output))
            self.assertIn("attach-patch-plan", {item["id"] for item in payload["azureActions"]})
            self.assertIn("comment-card", {item["id"] for item in payload["azureActions"]})

    def test_execute_n2_investigation_requires_destination_for_patch_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = {
                "supportContext": {
                    "symptom": "Erro tecnico sem card Azure e sem destino de arquivo.",
                    "evidence": [],
                }
            }

            result = run_capability(
                "execute-n2-investigation",
                fixture,
                ["--codebase-path", str(create_codebase(Path(tmpdir))), "--format", "json"],
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["patchPlan"]["readyForImplementation"])
            self.assertIn("--output", payload["patchPlan"]["blockingQuestions"][0])

    def test_patch_plan_masks_raw_cpf_from_card_and_support_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "patch_plan.md"
            fixture = {
                "work_item": {
                    "id": 8802,
                    "title": "CPF 12345678909 com falha",
                    "description": "Cliente 12345678909 nao avanca. Email pessoa@example.com.",
                    "state": "New",
                },
                "supportContext": {
                    "symptom": "CPF 12345678909 preso no onboarding.",
                    "evidence": ["Documento do CPF 12345678909 pendente."],
                },
            }

            result = run_capability(
                "generate-patch-plan",
                fixture,
                ["--codebase-path", str(create_codebase(Path(tmpdir))), "--output", str(output)],
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            content = output.read_text(encoding="utf-8")
            self.assertIn("123.***.***-09", content)
            self.assertNotIn("12345678909", content)
            self.assertNotIn("pessoa@example.com", content)

    def test_update_azure_workflow_output_does_not_write_patch_plan_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "actions.json"
            result = run_capability(
                "update-azure-workflow",
                {"work_item": {"id": 8803, "title": "Teste", "state": "New"}},
                ["--project", "Sustentacao", "--card", "8803", "--output", str(output), "--format", "json"],
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.exists())
            self.assertNotIn("# Patch Plan", output.read_text(encoding="utf-8"))

    def test_new_effectiveness_capabilities_return_structured_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            codebase = create_codebase(Path(tmpdir))
            fixture = {
                "n1_contract": {
                    "entities": {"cpfMasked": "123.***.***-09", "proposalNumber": "987654"},
                    "checks": [{"id": "bpo-proposal", "status": "pending"}],
                    "decision": {"status": "pending_n1_checks"},
                },
                "supportContext": {"evidence": ["BPO pendente em documentos."]},
            }
            expectations = {
                "validate-n1-handoff": "accepted",
                "select-specialist-checks": "selectedChecks",
                "execute-specialist-validation": "validations",
                "rank-code-findings": "rankedFindings",
                "build-reproduction-strategy": "testPlan",
                "review-patch-plan-readiness": "readyForImplementation",
                "update-n2-card-workflow": "azureActions",
            }

            for capability, expected_key in expectations.items():
                with self.subTest(capability=capability):
                    result = run_capability(
                        capability,
                        fixture,
                        [
                            "--project",
                            "Sustentacao",
                            "--card",
                            "8803",
                            "--codebase-path",
                            str(codebase),
                            "--format",
                            "json",
                        ],
                    )

                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(result.stdout)
                    self.assertIn(expected_key, payload)

    def test_execute_specialist_validation_executes_selected_agent_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = {
                "n1_contract": {
                    "entities": {"proposalNumber": "987654"},
                    "checks": [{"id": "bpo-proposal", "status": "pending"}],
                    "decision": {"status": "pending_n2"},
                },
                "supportContext": {
                    "symptom": "Proposta 987654 com pendencia BPO em documentos.",
                    "evidence": ["BPO retornou pendencia documental para proposta 987654."],
                },
                "proposal": {"numeroProposta": "987654"},
                "documents": {"files": []},
                "facts": {"proposal_number": "987654", "situation": "Pendente"},
                "inferences": {"attention_points": ["Pendente de documento."]},
            }

            result = run_capability(
                "execute-specialist-validation",
                fixture,
                [
                    "--project",
                    "Sustentacao",
                    "--card",
                    "8804",
                    "--codebase-path",
                    str(create_codebase(Path(tmpdir))),
                    "--execute",
                    "--format",
                    "json",
                ],
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            bpo_validation = next(item for item in payload["validations"] if item["agent"] == "bpo-analyser")
            self.assertEqual(bpo_validation["status"], "executed")
            self.assertIn("commandPreview", bpo_validation)
            self.assertIn("resultSummary", bpo_validation)

    def test_update_n2_card_workflow_includes_move_and_assign_actions(self) -> None:
        fixture = {
            "work_item": {
                "id": 8805,
                "title": "Card em N2",
                "state": "New",
                "board_column": "Triagem",
                "assigned_to": None,
            },
            "users": [{"unique_name": "ana@example.com", "display_name": "Ana"}],
        }

        result = run_capability(
            "update-n2-card-workflow",
            fixture,
            [
                "--project",
                "Sustentacao",
                "--card",
                "8805",
                "--target-state",
                "Active",
                "--target-column",
                "Analise N2",
                "--assign-to",
                "ana@example.com",
                "--format",
                "json",
            ],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        capabilities = {item["capability"] for item in payload["azureActions"]}
        self.assertIn("move-card", capabilities)
        self.assertIn("assign-card", capabilities)

    def test_patch_plan_not_ready_without_card_or_n1_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "patch_plan.md"
            result = run_capability(
                "generate-patch-plan",
                {
                    "supportContext": {
                        "symptom": "Erro ao avancar onboarding.",
                        "evidence": ["Falha sem contrato N1 e sem card Azure carregado."],
                    }
                },
                [
                    "--codebase-path",
                    str(create_codebase(Path(tmpdir))),
                    "--output",
                    str(output),
                    "--format",
                    "json",
                ],
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["patchPlan"]["readyForImplementation"])
            self.assertTrue(
                any("N1" in item or "Azure" in item for item in payload["patchPlan"]["blockingQuestions"])
            )


def create_codebase(tmpdir: Path) -> Path:
    codebase = tmpdir / "sample-app"
    source = codebase / "src"
    tests = codebase / "tests"
    source.mkdir(parents=True)
    tests.mkdir()
    (source / "onboarding_service.py").write_text(
        "\n".join(
            [
                "class OnboardingService:",
                "    def advance_document_step(self, proposal):",
                "        if proposal.bpo_status == 'pending_documents':",
                "            return 'blocked'",
                "        return 'advanced'",
            ]
        ),
        encoding="utf-8",
    )
    (tests / "test_onboarding_service.py").write_text(
        "def test_advance_document_step_blocks_pending_documents():\n    assert True\n",
        encoding="utf-8",
    )
    return codebase


def run_capability(capability: str, fixture: dict, extra_args: list[str]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = Path(tmpdir) / "fixture.json"
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(CLI),
                "run",
                "n2-support-agent",
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
