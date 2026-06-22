#!/usr/bin/env python3
"""Tests for trace-request runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class TraceRequestRunnerTest(unittest.TestCase):
    def test_renders_trace_from_fixture(self) -> None:
        fixture = {
            "identifier": "abc-123",
            "events": [
                {"timestamp": 2, "log_stream_name": "s1", "message": "request abc-123 finished"},
                {"timestamp": 1, "log_stream_name": "s1", "message": "request abc-123 started"},
            ],
        }
        result = run_fixture(fixture)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Request Trace", result.stdout)
        self.assertIn("Eventos encontrados: 2", result.stdout)

    def test_masks_sensitive_identifier_from_fixture_output(self) -> None:
        fixture = {
            "identifier": "user@example.com",
            "events": [
                {"timestamp": 1, "log_stream_name": "s1", "message": "request user@example.com failed"},
            ],
        }
        result = run_fixture(fixture)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("user@example.com", result.stdout)
        self.assertIn("u***@example.com", result.stdout)

    def test_rejects_sensitive_cli_identifier(self) -> None:
        fixture = {
            "events": [
                {"timestamp": 1, "log_stream_name": "s1", "message": "request user@example.com failed"},
            ],
        }
        result = run_fixture(fixture, "--identifier", "user@example.com")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sensitive identifier", result.stderr)


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
