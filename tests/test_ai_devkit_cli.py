#!/usr/bin/env python3
"""Tests for the root ai-devkit CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "ai-devkit"


class AiDevKitCliTest(unittest.TestCase):
    def test_lists_available_agents(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CLI), "--json", "agents"],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        agents = {item["id"] for item in payload["items"]}
        self.assertIn("azure-devops-orchestrator", agents)
        self.assertIn("aws-cloudwatch-log-analyzer", agents)

    def test_lists_all_aws_cloudwatch_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "aws-cloudwatch-log-analyzer",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        capabilities = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertEqual(
            capabilities,
            {
                "analyze-service-error",
                "correlate-azure-card-logs",
                "detect-error-patterns",
                "extract-log-samples",
                "generate-incident-report",
                "list-log-groups",
                "search-log-events",
                "trace-request",
            },
        )

    def test_all_aws_cloudwatch_capabilities_have_runner(self) -> None:
        for capability in (
            "analyze-service-error",
            "correlate-azure-card-logs",
            "detect-error-patterns",
            "extract-log-samples",
            "generate-incident-report",
            "list-log-groups",
            "search-log-events",
            "trace-request",
        ):
            with self.subTest(capability=capability):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--json",
                        "inspect",
                        "aws-cloudwatch-log-analyzer",
                        capability,
                    ],
                    cwd=ROOT,
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                runner = payload["capability"]["entrypoint"]["runner"]
                self.assertTrue(runner["exists"])

    def test_lists_all_azure_devops_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "azure-devops-orchestrator",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        capabilities = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertEqual(
            capabilities,
            {
                "alterar-tags-card",
                "atribuir-card",
                "comentar-card",
                "gerar-relatorio-cards",
                "ler-card",
                "listar-cards",
                "mover-card",
                "preparar-analise-card",
            },
        )

    def test_all_azure_devops_capabilities_have_runner(self) -> None:
        for capability in (
            "alterar-tags-card",
            "atribuir-card",
            "comentar-card",
            "gerar-relatorio-cards",
            "ler-card",
            "listar-cards",
            "mover-card",
            "preparar-analise-card",
        ):
            with self.subTest(capability=capability):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--json",
                        "inspect",
                        "azure-devops-orchestrator",
                        capability,
                    ],
                    cwd=ROOT,
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                runner = payload["capability"]["entrypoint"]["runner"]
                self.assertTrue(runner["exists"])

    def test_run_ler_card_with_fixture(self) -> None:
        fixture = {
            "work_item": {
                "id": 456,
                "work_item_type": "Bug",
                "title": "Corrigir erro no login",
                "state": "New",
                "assigned_to": "bia@example.com",
                "tags": ["bug"],
                "description": "Login falha quando o token expira.",
                "acceptance_criteria": "Usuario deve ser redirecionado para autenticar novamente.",
            },
            "comments": {"work_item_id": 456, "count": 0, "comments": []},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "card.json"
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "azure-devops-orchestrator",
                    "ler-card",
                    "--project",
                    "Projeto A",
                    "--fixture",
                    str(fixture_path),
                    "--include-comments",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Analise do Card", result.stdout)
        self.assertIn("- ID: 456", result.stdout)
        self.assertIn("- Titulo: Corrigir erro no login", result.stdout)


if __name__ == "__main__":
    unittest.main()
