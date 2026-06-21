#!/usr/bin/env python3
"""Smoke tests for BPO Analyser runners through ai-devkit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


PROPOSAL = {
    "proposal_number": "123456",
    "contract_number": "ABC123",
    "formalization_id": "789",
    "processing_status": {"status": True, "error_message": ""},
    "situation": "Pendente",
    "activity": "Analise de documentos",
    "situation_date": "2026-06-20T10:00:00",
    "customer_name": "Ana Silva",
    "cpf": "12345678901",
    "product_name": "Cartao Beneficio",
    "proposal_type": "Saque",
    "amounts": {"requested": 1200.0, "released": 1000.5},
    "observations": [{"date": "2026-06-20", "text": "Documento pendente"}],
}


DOCUMENTS = {
    "proposal_number": "123456",
    "requested_document_type": "Nao_Definido",
    "processing_status": {"status": True, "error_message": ""},
    "count": 1,
    "files": [
        {
            "proposal_number": 123456,
            "file_name": "ccb.pdf",
            "document_type": "CCB_Negociavel",
            "extension_file_type": "PDF",
            "size": 2048,
            "has_file_base64": True,
        }
    ],
}

CPF_PROPOSALS = {
    "cpf": "12345678901",
    "masked_cpf": "123.***.***-01",
    "count": 2,
    "proposals": [
        {
            "proposal_number": 123456,
            "situation": "INT",
            "situation_kind": "integrada",
            "proposal_type": "3",
            "is_eligible": True,
            "last_due_date": "2026-12-10T00:00:00",
            "withdraw_limit": 500.0,
            "released_amount": 1000.0,
            "agency": "Orgao XPTO",
            "customer": {"cpf": "12345678901", "name": "Ana Silva", "registration": "9988"},
        },
        {
            "proposal_number": 123457,
            "situation": "PEN",
            "situation_kind": "pendente",
            "proposal_type": "3",
            "is_eligible": False,
            "last_due_date": "2027-01-10T00:00:00",
            "withdraw_limit": 0,
            "released_amount": 0,
            "customer": {"cpf": "12345678901", "name": "Ana Silva"},
        },
    ],
}

CPF_ANALYSIS = {
    "cpf": "12345678901",
    "masked_cpf": "123.***.***-01",
    "proposals": CPF_PROPOSALS["proposals"],
    "facts": {
        "total": 2,
        "eligible_count": 1,
        "under_analysis_count": 1,
        "rejected_count": 0,
        "latest_integrated_or_approved": CPF_PROPOSALS["proposals"][0],
    },
    "groups": {
        "eligible": [CPF_PROPOSALS["proposals"][0]],
        "under_analysis": [CPF_PROPOSALS["proposals"][1]],
        "rejected": [],
    },
    "inferences": {
        "attention_points": ["Existe proposta em analise para o CPF."],
        "has_blocking_signals": True,
    },
}


class BpoRunnerSmokeTest(unittest.TestCase):
    def test_test_connection_from_fixture(self) -> None:
        result = run_capability(
            "test-connection",
            {
                "configured": True,
                "user_configured": True,
                "password_configured": True,
                "timeout": 30,
                "default_document_type": "Nao_Definido",
                "endpoints": {
                    "servico_api": {"configured": True, "url": "https://example.com/ServicoAPI"}
                },
            },
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Diagnostico BPO", result.stdout)
        self.assertIn("servico_api", result.stdout)

    def test_consult_proposal_from_fixture_masks_cpf(self) -> None:
        result = run_capability("consult-proposal", PROPOSAL)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Consulta de Proposta BPO", result.stdout)
        self.assertIn("- Proposta: 123456", result.stdout)
        self.assertIn("123.***.***-01", result.stdout)
        self.assertNotIn("12345678901", result.stdout)

    def test_consult_attached_documents_from_fixture(self) -> None:
        result = run_capability("consult-attached-documents", DOCUMENTS)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Documentos Anexados BPO", result.stdout)
        self.assertIn("ccb.pdf", result.stdout)

    def test_list_proposals_by_cpf_from_fixture_masks_cpf(self) -> None:
        result = run_capability("list-proposals-by-cpf", CPF_PROPOSALS)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Propostas BPO por CPF", result.stdout)
        self.assertIn("123.***.***-01", result.stdout)
        self.assertIn("123456", result.stdout)
        self.assertNotIn("12345678901", result.stdout)

    def test_analyze_cpf_proposals_from_fixture(self) -> None:
        result = run_capability("analyze-cpf-proposals", CPF_ANALYSIS)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Analise de Propostas BPO por CPF", result.stdout)
        self.assertIn("- Elegiveis: 1", result.stdout)
        self.assertIn("Existe proposta em analise", result.stdout)

    def test_find_latest_proposal_by_cpf_from_fixture(self) -> None:
        result = run_capability(
            "find-latest-proposal-by-cpf",
            {
                "cpf": "12345678901",
                "masked_cpf": "123.***.***-01",
                "selected": CPF_PROPOSALS["proposals"][0],
                "criteria": "situacao INT/APR com data_ultimo_vencimento mais recente",
                "source_count": 2,
                "eligible_count": 1,
            },
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Proposta BPO Mais Recente por CPF", result.stdout)
        self.assertIn("- Proposta: 123456", result.stdout)

    def test_analyze_proposal_from_fixture(self) -> None:
        result = run_capability(
            "analyze-proposal",
            {
                "proposal": PROPOSAL,
                "documents": DOCUMENTS,
                "facts": {
                    "proposal_number": "123456",
                    "situation": "Pendente",
                    "activity": "Analise de documentos",
                    "observation_count": 1,
                    "document_count": 1,
                    "document_types": ["CCB_Negociavel"],
                },
                "inferences": {"attention_points": [], "has_blocking_signals": False},
            },
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Analise de Proposta BPO", result.stdout)
        self.assertIn("Nenhum ponto de atencao", result.stdout)

    def test_analyze_proposal_json_from_fixture_masks_sensitive_fields(self) -> None:
        result = run_capability(
            "analyze-proposal",
            {
                "proposal": PROPOSAL,
                "documents": {
                    **DOCUMENTS,
                    "files": [
                        {
                            **DOCUMENTS["files"][0],
                            "file_base64": "raw-document-content",
                        }
                    ],
                },
                "facts": {
                    "proposal_number": "123456",
                    "situation": "Pendente",
                    "activity": "Analise de documentos",
                    "observation_count": 1,
                    "document_count": 1,
                    "document_types": ["CCB_Negociavel"],
                },
                "inferences": {"attention_points": [], "has_blocking_signals": False},
            },
            ["--format", "json"],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["proposal"]["proposal_number"], "123456")
        self.assertEqual(payload["proposal"]["cpf"], "123.***.***-01")
        self.assertNotIn("12345678901", result.stdout)
        self.assertNotIn("raw-document-content", result.stdout)


def run_capability(capability: str, fixture: dict, extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = Path(tmpdir) / "fixture.json"
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(CLI),
                "run",
                "bpo-analyser",
                capability,
                "--fixture",
                str(fixture_path),
                *(extra_args or []),
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


if __name__ == "__main__":
    unittest.main()
