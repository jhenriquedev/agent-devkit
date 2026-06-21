#!/usr/bin/env python3
"""Tests for the listar-cards capability runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class ListarCardsRunnerTest(unittest.TestCase):
    def test_renders_cards_from_fixture(self) -> None:
        fixture = {
            "count": 1,
            "wiql": "SELECT [System.Id] FROM WorkItems",
            "items": [
                {
                    "id": 123,
                    "work_item_type": "Issue",
                    "title": "Alerta MCC API",
                    "state": "To Do",
                    "assigned_to": None,
                    "tags": ["prd", "Warning"],
                }
            ],
        }

        result = run_fixture(fixture, "--limit", "10")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Cards Listados", result.stdout)
        self.assertIn("Alerta MCC API", result.stdout)
        self.assertIn("prd, Warning", result.stdout)


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
