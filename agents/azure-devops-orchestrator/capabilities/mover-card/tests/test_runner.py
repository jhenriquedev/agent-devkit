#!/usr/bin/env python3
"""Tests for the mover-card capability runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class MoverCardRunnerTest(unittest.TestCase):
    def test_renders_move_preview_from_fixture(self) -> None:
        fixture = {
            "work_item": {
                "id": 123,
                "title": "Alerta MCC API",
                "state": "To Do",
                "board_column": "Backlog",
            }
        }

        result = run_fixture(fixture, "--state", "Active", "--board-column", "Doing")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Movimentacao do Card", result.stdout)
        self.assertIn("Estado atual: To Do", result.stdout)
        self.assertIn("Estado alvo: Active", result.stdout)


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
