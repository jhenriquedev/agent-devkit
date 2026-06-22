#!/usr/bin/env python3
"""Tests for run-insights-query runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class RunInsightsQueryRunnerTest(unittest.TestCase):
    def test_renders_started_query_from_fixture(self) -> None:
        fixture = {
            "region": "us-east-1",
            "log_group": "/aws/app/service",
            "queryId": "abc-123",
        }

        result = run_fixture(fixture)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# CloudWatch Logs Insights Query", result.stdout)
        self.assertIn("abc-123", result.stdout)
        self.assertIn("Iniciada", result.stdout)

    def test_renders_query_results_from_fixture(self) -> None:
        fixture = {
            "region": "us-east-1",
            "query_id": "abc-123",
            "status": "Complete",
            "results": [
                [
                    {"field": "@timestamp", "value": "2026-06-22T10:00:00Z"},
                    {"field": "message", "value": "ERROR timeout"},
                ]
            ],
            "statistics": {"recordsMatched": 1},
        }

        result = run_fixture(fixture)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Complete", result.stdout)
        self.assertIn("ERROR timeout", result.stdout)
        self.assertIn("recordsMatched", result.stdout)


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
