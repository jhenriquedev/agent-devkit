#!/usr/bin/env python3
"""Tests for list-log-streams runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class ListLogStreamsRunnerTest(unittest.TestCase):
    def test_renders_log_streams_from_fixture(self) -> None:
        fixture = {
            "region": "us-east-1",
            "log_group": "/aws/app/service",
            "log_streams": [
                {
                    "logStreamName": "service/2026/06/22",
                    "lastEventTimestamp": 1790000000000,
                    "storedBytes": 2048,
                }
            ],
        }

        result = run_fixture(fixture)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Log Streams", result.stdout)
        self.assertIn("service/2026/06/22", result.stdout)
        self.assertIn("2048", result.stdout)


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
