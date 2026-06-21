#!/usr/bin/env python3
"""Tests for list-log-groups runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class ListLogGroupsRunnerTest(unittest.TestCase):
    def test_renders_log_groups_from_fixture(self) -> None:
        fixture = {
            "region": "us-east-1",
            "log_groups": [
                {"log_group_name": "/aws/app/service", "retention_in_days": 14, "stored_bytes": 123}
            ],
        }
        result = run_fixture(fixture)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Log Groups", result.stdout)
        self.assertIn("/aws/app/service", result.stdout)


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
