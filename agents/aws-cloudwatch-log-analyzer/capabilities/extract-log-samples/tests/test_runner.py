#!/usr/bin/env python3
"""Tests for extract-log-samples runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class ExtractLogSamplesRunnerTest(unittest.TestCase):
    def test_renders_samples_from_fixture(self) -> None:
        fixture = {
            "events": [
                {"timestamp": 1, "log_stream_name": "s1", "message": "first"},
                {"timestamp": 2, "log_stream_name": "s1", "message": "second"},
            ],
        }
        result = run_fixture(fixture, "--sample-size", "1", "--strategy", "last")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Log Samples", result.stdout)
        self.assertIn("second", result.stdout)
        self.assertNotIn("first |", result.stdout)


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
