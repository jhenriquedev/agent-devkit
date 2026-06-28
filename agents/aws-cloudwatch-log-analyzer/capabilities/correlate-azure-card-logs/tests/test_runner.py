#!/usr/bin/env python3
"""Tests for correlate-azure-card-logs runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class CorrelateAzureCardLogsRunnerTest(unittest.TestCase):
    def test_renders_correlation_from_fixture(self) -> None:
        fixture = {
            "card": {"id": 7710, "project": "SupportProject", "title": "Health warning"},
            "cloudwatch": {
                "region": "us-east-1",
                "log_group": "/aws/app/service",
                "events": [{"timestamp": 1, "log_stream_name": "s1", "message": "WARNING health"}],
            },
        }
        result = run_fixture(fixture, "--include-comment-draft")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Azure Card Log Correlation", result.stdout)
        self.assertIn("Work item: 7710", result.stdout)
        self.assertIn("Comentario sugerido", result.stdout)


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
