#!/usr/bin/env python3
"""Tests for analyze-service-error runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class AnalyzeServiceErrorRunnerTest(unittest.TestCase):
    def test_renders_error_analysis_from_fixture(self) -> None:
        fixture = {
            "service": "example-api",
            "environment": "prd",
            "events": [
                {"timestamp": 1, "log_stream_name": "s1", "message": "POST /api/test 500 ERROR timeout"}
            ],
        }
        result = run_fixture(fixture)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Service Error Analysis", result.stdout)
        self.assertIn("Eventos de erro: 1", result.stdout)
        self.assertIn("timeout", result.stdout.lower())


def run_fixture(fixture: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "fixture.json"
        path.write_text(json.dumps(fixture), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(RUNNER), "--fixture", str(path)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


if __name__ == "__main__":
    unittest.main()
