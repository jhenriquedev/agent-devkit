#!/usr/bin/env python3
"""Tests for the attach-file capability runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class AttachFileRunnerTest(unittest.TestCase):
    def test_renders_attachment_plan_from_fixture(self) -> None:
        fixture = {
            "work_item": {
                "id": 321,
                "title": "Anexar evidencia de deploy",
                "state": "Active",
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            fixture_path = tmpdir_path / "fixture.json"
            file_path = tmpdir_path / "evidencia.txt"
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
            file_path.write_text("deploy ok", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--fixture",
                    str(fixture_path),
                    "--file",
                    str(file_path),
                    "--comment",
                    "Evidencia de deploy.",
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Card Attachment", result.stdout)
        self.assertIn("- Card: 321", result.stdout)
        self.assertIn("- Name: evidencia.txt", result.stdout)
        self.assertIn("- Comment: Evidencia de deploy.", result.stdout)
        self.assertIn("- Status: planned", result.stdout)
        self.assertIn("Re-run with `--execute`", result.stdout)

    def test_rejects_missing_file_before_loading_card(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--fixture",
                "unused.json",
                "--file",
                "missing.txt",
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("file not found", result.stderr)


if __name__ == "__main__":
    unittest.main()
