#!/usr/bin/env python3
"""Tests for the ler-card capability runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CAPABILITY_DIR = Path(__file__).resolve().parents[1]
RUNNER = CAPABILITY_DIR / "runner.py"


class LerCardRunnerTest(unittest.TestCase):
    def test_renders_card_analysis_from_fixture(self) -> None:
        fixture = {
            "work_item": {
                "id": 123,
                "work_item_type": "User Story",
                "title": "Permitir login com SSO",
                "state": "Active",
                "board_column": "Doing",
                "created_date": "2026-06-20T10:00:00Z",
                "changed_date": "2026-06-20T11:00:00Z",
                "assigned_to": "ana@example.com",
                "tags": ["sso", "auth"],
                "description": "Usuario deve conseguir entrar via provedor corporativo.",
                "acceptance_criteria": None,
                "relations": [
                    {
                        "rel": "AttachedFile",
                        "attributes": {
                            "name": "evidencia.json",
                            "comment": "Arquivo de evidencia.",
                        },
                    }
                ],
                "url": "https://dev.azure.com/example/project/_workitems/edit/123",
            },
            "comments": {
                "work_item_id": 123,
                "count": 1,
                "comments": [
                    {
                        "id": 1,
                        "author": "joao@example.com",
                        "created_at": "2026-06-20T10:00:00Z",
                        "text": "Ainda falta definir criterios de aceite.",
                    }
                ],
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "card.json"
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--fixture",
                    str(fixture_path),
                    "--include-comments",
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Analise do Card", result.stdout)
        self.assertIn("- ID: 123", result.stdout)
        self.assertIn("- Titulo: Permitir login com SSO", result.stdout)
        self.assertIn("- Coluna atual: Doing", result.stdout)
        self.assertIn("- Criado em: 2026-06-20T10:00:00Z", result.stdout)
        self.assertIn("- Tags: sso, auth", result.stdout)
        self.assertIn("- evidencia.json - Arquivo de evidencia.", result.stdout)
        self.assertIn("Ainda falta definir criterios de aceite.", result.stdout)
        self.assertIn("Criterios de aceite ausentes.", result.stdout)
        self.assertIn("Separar fatos coletados de inferencias.", result.stdout)


if __name__ == "__main__":
    unittest.main()
