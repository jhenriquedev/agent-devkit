#!/usr/bin/env python3
"""Tests for the preparar-analise-card capability runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runner.py"


class PrepararAnaliseCardRunnerTest(unittest.TestCase):
    def test_renders_operational_analysis_from_fixture(self) -> None:
        fixture = {
            "work_item": {
                "id": 123,
                "title": "Elastic Beanstalk warning",
                "state": "To Do",
                "description": "Elastic Beanstalk reportou health warning no CloudWatch.",
                "tags": ["Warning", "ElasticBeanstalk"],
                "assigned_to": None,
            },
            "comments": {"comments": []},
        }

        result = run_fixture(fixture, "--include-comment-draft")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Analise Operacional do Card", result.stdout)
        self.assertIn("Tipo identificado: bug/incidente", result.stdout)
        self.assertIn("Comentario sugerido", result.stdout)


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
