#!/usr/bin/env python3
"""Tests for the gerar-relatorio-cards capability runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class GerarRelatorioCardsRunnerTest(unittest.TestCase):
    def test_renders_consolidated_report_from_fixture(self) -> None:
        fixture = {
            "project": "Sustentacao",
            "limit": 10,
            "cards": [
                {
                    "work_item": {
                        "id": 101,
                        "work_item_type": "Issue",
                        "title": "Alerta MCC API",
                        "state": "To Do",
                        "board_column": "Backlog",
                        "assigned_to": None,
                        "tags": ["prd", "Warning"],
                        "description": "Elastic Beanstalk health warning.",
                        "acceptance_criteria": None,
                        "relations": [
                            {
                                "rel": "AttachedFile",
                                "attributes": {"name": "evidencia.json"},
                            }
                        ],
                    },
                    "comments": {
                        "comments": [
                            {"id": 1, "text": "Criado automaticamente."}
                        ]
                    },
                },
                {
                    "work_item": {
                        "id": 102,
                        "work_item_type": "Bug",
                        "title": "Erro no login",
                        "state": "Active",
                        "board_column": "Doing",
                        "assigned_to": "ana@example.com",
                        "tags": ["Bugfix"],
                        "description": "",
                        "acceptance_criteria": "Usuario reautentica.",
                        "relations": [],
                    },
                    "comments": {"comments": []},
                },
            ],
        }

        result = run_fixture(fixture)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Relatorio de Cards Azure DevOps", result.stdout)
        self.assertIn("- Total de cards: 2", result.stdout)
        self.assertIn("- Sem responsavel: 1", result.stdout)
        self.assertIn("- Sem criterios: 1", result.stdout)
        self.assertIn("| 101 | Issue | Alerta MCC API", result.stdout)
        self.assertIn("### Card 102 - Erro no login", result.stdout)

    def test_can_omit_details_and_write_output(self) -> None:
        fixture = {
            "project": "Sustentacao",
            "cards": [
                {
                    "work_item": {
                        "id": 101,
                        "title": "Alerta",
                        "state": "To Do",
                        "tags": [],
                    },
                    "comments": {"comments": []},
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "fixture.json"
            output_path = Path(tmpdir) / "report.md"
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--fixture",
                    str(fixture_path),
                    "--no-include-details",
                    "--output",
                    str(output_path),
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = output_path.read_text(encoding="utf-8")
            self.assertIn("# Relatorio de Cards Azure DevOps", report)
            self.assertNotIn("### Card 101", report)


def run_fixture(fixture: dict, *args: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = Path(tmpdir) / "fixture.json"
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(RUNNER), "--fixture", str(fixture_path), *args],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


if __name__ == "__main__":
    unittest.main()
