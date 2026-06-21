#!/usr/bin/env python3
"""Tests for the update-card-tags capability runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class UpdateCardTagsRunnerTest(unittest.TestCase):
    def test_renders_tag_diff_from_fixture(self) -> None:
        fixture = {
            "work_item": {
                "id": 123,
                "title": "Alerta MCC API",
                "tags": ["prd", "Warning"],
            }
        }

        result = run_fixture(fixture, "--add-tag", "Bugfix", "--remove-tag", "Warning")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Card Tag Update", result.stdout)
        self.assertIn("Current tags: prd, Warning", result.stdout)
        self.assertIn("Final tags: prd, Bugfix", result.stdout)


def run_fixture(fixture: dict, *args: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = Path(tmpdir) / "fixture.json"
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(RUNNER), "--fixture", str(fixture_path), *args],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


if __name__ == "__main__":
    unittest.main()
