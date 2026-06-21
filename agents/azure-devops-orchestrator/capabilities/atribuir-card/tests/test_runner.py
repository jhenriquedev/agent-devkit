#!/usr/bin/env python3
"""Tests for the atribuir-card capability runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class AtribuirCardRunnerTest(unittest.TestCase):
    def test_renders_assignment_preview_from_fixture(self) -> None:
        fixture = {
            "work_item": {
                "id": 123,
                "title": "Alerta MCC API",
                "assigned_to": None,
            },
            "users": [
                {
                    "display_name": "Ana Silva",
                    "unique_name": "ana@example.com",
                    "email": "ana@example.com",
                }
            ],
        }

        result = run_fixture(fixture, "--assignee", "ana@example.com")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Atribuicao do Card", result.stdout)
        self.assertIn("Responsavel alvo: ana@example.com", result.stdout)
        self.assertIn("Reexecute com `--execute`", result.stdout)


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
