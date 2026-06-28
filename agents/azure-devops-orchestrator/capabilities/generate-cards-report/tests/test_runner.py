#!/usr/bin/env python3
"""Tests for the generate-cards-report capability runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class GenerateCardsReportRunnerTest(unittest.TestCase):
    def test_renders_consolidated_report_from_fixture(self) -> None:
        fixture = {
            "project": "SupportProject",
            "limit": 10,
            "cards": [
                {
                    "work_item": {
                        "id": 101,
                        "work_item_type": "Issue",
                        "title": "Service API alert",
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
        self.assertIn("# Azure DevOps Cards Report", result.stdout)
        self.assertIn("- Total de cards: 2", result.stdout)
        self.assertIn("- Without assignee: 1", result.stdout)
        self.assertIn("- Without acceptance criteria: 1", result.stdout)
        self.assertIn("| 101 | Issue | Service API alert", result.stdout)
        self.assertIn("### Card 102 - Erro no login", result.stdout)

    def test_can_omit_details_and_write_output(self) -> None:
        fixture = {
            "project": "SupportProject",
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
            self.assertIn("# Azure DevOps Cards Report", report)
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
