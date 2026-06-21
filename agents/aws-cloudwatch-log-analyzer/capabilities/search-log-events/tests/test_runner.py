#!/usr/bin/env python3
"""Tests for search-log-events runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class SearchLogEventsRunnerTest(unittest.TestCase):
    def test_renders_events_from_fixture(self) -> None:
        fixture = {
            "region": "us-east-1",
            "log_group": "/aws/app/service",
            "events": [{"timestamp": 1, "log_stream_name": "s1", "message": "ERROR boom"}],
        }
        result = run_fixture(fixture)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Log Events", result.stdout)
        self.assertIn("ERROR boom", result.stdout)


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
