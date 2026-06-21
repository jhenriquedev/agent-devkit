#!/usr/bin/env python3
"""Tests for detect-error-patterns runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class DetectErrorPatternsRunnerTest(unittest.TestCase):
    def test_renders_patterns_from_fixture(self) -> None:
        fixture = {
            "events": [
                {"timestamp": 1, "log_stream_name": "s1", "message": "GET /a 500 ERROR"},
                {"timestamp": 2, "log_stream_name": "s1", "message": "GET /a 500 ERROR"},
            ],
        }
        result = run_fixture(fixture, "--group-by", "status_code")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Error Patterns", result.stdout)
        self.assertIn("- 500: 2", result.stdout)


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
