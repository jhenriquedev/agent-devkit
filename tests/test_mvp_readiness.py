#!/usr/bin/env python3
"""Tests for the MVP readiness script."""

from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MVP_READINESS = ROOT / "scripts" / "mvp-readiness.py"
RELEASE_GATE = ROOT / "scripts" / "release-gate.py"


def load_release_gate_module():
    spec = importlib.util.spec_from_file_location("release_gate", RELEASE_GATE)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class MvpReadinessTest(unittest.TestCase):
    def test_mvp_readiness_passes_and_reports_expected_checks(self) -> None:
        result = subprocess.run(
            [sys.executable, str(MVP_READINESS), "--json"],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=90,
        )

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "mvp-readiness")
        self.assertEqual(payload["status"], "ok")
        self.assertFalse(payload["errors"])
        checks = {item["name"]: item for item in payload["checks"]}
        for name in (
            "agent version",
            "commands list",
            "llm backends list",
            "providers list",
            "project install",
            "doctor clean project",
            "run fallback without provider",
            "agent without llm",
            "repo strict validation",
        ):
            self.assertEqual(checks[name]["status"], "ok")

    def test_release_gate_quick_passes_and_reports_expected_checks(self) -> None:
        result = subprocess.run(
            [sys.executable, str(RELEASE_GATE), "--quick", "--json"],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
        )

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "release-gate")
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["quick"])
        checks = {item["name"]: item for item in payload["checks"]}
        self.assertEqual(checks["agent version"]["status"], "ok")
        self.assertEqual(checks["repo strict validation"]["status"], "ok")
        self.assertEqual(checks["catalog snapshot"]["status"], "ok")
        self.assertEqual(checks["mvp readiness"]["status"], "ok")
        self.assertIn(checks["claude skill validation"]["status"], {"ok", "skipped"})
        self.assertEqual(checks["full unittest suite"]["status"], "skipped")

    def test_release_gate_unittest_discovery_ignores_generated_runtime(self) -> None:
        release_gate = load_release_gate_module()

        command = release_gate.unittest_command()

        self.assertIn("tests/test_aikit_cli.py", command)
        self.assertFalse(any("vendor/" in item for item in command))
        self.assertFalse(any(item.startswith("tooling/agent-devkit/runtime/") for item in command))


if __name__ == "__main__":
    unittest.main()
