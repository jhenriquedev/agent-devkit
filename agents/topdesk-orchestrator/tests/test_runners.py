#!/usr/bin/env python3
"""Smoke tests for TOPdesk Orchestrator runners through ai-devkit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


INCIDENT = {
    "id": "abc-123",
    "number": "I 2606 001",
    "brief_description": "Erro",
    "request": "Nao funciona",
    "status": "Open",
    "category": "",
    "priority": "",
    "operator_group": "",
    "operator": "",
    "caller": "Ana Silva",
}

INCIDENTS = {
    "items": [
        {
            **INCIDENT,
            "brief_description": "Erro no acesso ao portal",
            "priority": "P2",
            "operator_group": "Service Desk",
        },
        {
            "id": "def-456",
            "number": "I 2606 002",
            "brief_description": "Solicitar liberacao de acesso",
            "status": "Closed",
            "priority": "P4",
            "operator_group": "",
        },
    ]
}


class TopdeskRunnerSmokeTest(unittest.TestCase):
    def test_list_incidents_from_fixture(self) -> None:
        result = run_capability("list-incidents", INCIDENTS)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# TOPdesk Incidents", result.stdout)
        self.assertIn("I 2606 001", result.stdout)

    def test_read_incident_from_fixture(self) -> None:
        fixture = {
            "incident": INCIDENT,
            "progress_trail": {"entries": [{"date": "2026-06-21", "text": "Criado"}]},
        }
        result = run_capability("read-incident", fixture, "--include-progress-trail")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# TOPdesk Incident", result.stdout)
        self.assertIn("- Numero: I 2606 001", result.stdout)
        self.assertIn("Criado", result.stdout)

    def test_analyze_incident_insufficiency_from_fixture(self) -> None:
        result = run_capability("analyze-incident-insufficiency", {"incident": INCIDENT})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Analise de Insuficiencia do Incidente", result.stdout)
        self.assertIn("- briefDescription", result.stdout)
        self.assertIn("- request", result.stdout)

    def test_create_incident_dry_run_from_fixture(self) -> None:
        fixture = {"result": {"dry_run": True, "operation": "create_incident"}}
        result = run_capability(
            "create-incident",
            fixture,
            "--brief-description",
            "Erro no portal",
            "--request",
            "Usuario informa erro ao acessar o portal corporativo.",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Criacao de Incidente TOPdesk", result.stdout)
        self.assertIn("- Dry-run: True", result.stdout)

    def test_update_incident_dry_run_from_fixture(self) -> None:
        fixture = {"result": {"dry_run": True, "target": "abc-123"}}
        result = run_capability(
            "update-incident",
            fixture,
            "--id",
            "abc-123",
            "--fields-json",
            '{"status":{"name":"In progress"}}',
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Atualizacao de Incidente TOPdesk", result.stdout)
        self.assertIn("- Dry-run: True", result.stdout)

    def test_request_more_info_dry_run_from_fixture(self) -> None:
        result = run_capability("request-more-info", {"incident": INCIDENT})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Pedido de Mais Informacoes", result.stdout)
        self.assertIn("- Dry-run: True", result.stdout)
        self.assertIn("Descreva em uma frase", result.stdout)

    def test_incident_report_from_fixture(self) -> None:
        result = run_capability("incident-report", INCIDENTS)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Relatorio de Incidentes TOPdesk", result.stdout)
        self.assertIn("## Por status", result.stdout)
        self.assertIn("- Open: 1", result.stdout)


def run_capability(
    capability: str,
    fixture: dict,
    *extra_args: str,
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = Path(tmpdir) / "fixture.json"
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(CLI),
                "run",
                "topdesk-orchestrator",
                capability,
                "--fixture",
                str(fixture_path),
                *extra_args,
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


if __name__ == "__main__":
    unittest.main()
