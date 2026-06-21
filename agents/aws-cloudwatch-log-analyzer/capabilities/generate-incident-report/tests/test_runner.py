#!/usr/bin/env python3
"""Tests for generate-incident-report runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class GenerateIncidentReportRunnerTest(unittest.TestCase):
    def test_renders_incident_report_from_fixture(self) -> None:
        fixture = {
            "service": "mcc-api",
            "environment": "prd",
            "incident_title": "Health warning",
            "events": [{"timestamp": 1, "log_stream_name": "s1", "message": "health WARNING"}],
        }
        result = run_fixture(fixture, "--include-samples")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Incident Report", result.stdout)
        self.assertIn("Health warning", result.stdout)
        self.assertIn("## Amostras", result.stdout)


def run_fixture(fixture: dict, *args: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "fixture.json"
        path.write_text(json.dumps(fixture), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(RUNNER), "--fixture", str(path), *args],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


if __name__ == "__main__":
    unittest.main()
