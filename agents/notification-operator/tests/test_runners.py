#!/usr/bin/env python3
"""Runner contracts for notification-operator."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FORMAT_RUNNER = ROOT / "notification-operator" / "capabilities" / "format-task-completion-notification" / "runner.py"
SEND_RUNNER = ROOT / "notification-operator" / "capabilities" / "send-task-completion-notification" / "runner.py"
CONFIGURE_RUNNER = ROOT / "notification-operator" / "capabilities" / "configure-notification-channel" / "runner.py"
RUNNER_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_RUNNER_TIMEOUT_SECONDS", "60"))


class NotificationOperatorRunnerTest(unittest.TestCase):
    def run_python(self, script: Path, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *args],
            cwd=ROOT.parents[0],
            env=os.environ | env,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=RUNNER_TIMEOUT_SECONDS,
        )

    def test_format_runner_returns_canonical_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_python(
                FORMAT_RUNNER,
                "--summary",
                "done",
                "--event",
                "task.completed",
                "--task-id",
                "t1",
                env={"AI_DEVKIT_CONFIG_HOME": tmpdir},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "notification-event")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["task_id"], "t1")

    def test_send_runner_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_python(
                SEND_RUNNER,
                "--summary",
                "done",
                "--channel",
                "terminal",
                env={"AI_DEVKIT_CONFIG_HOME": tmpdir},
            )

        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "needs-confirmation")
        self.assertEqual(payload["write_policy"], "confirm")

    def test_send_runner_can_send_terminal_when_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_python(
                SEND_RUNNER,
                "--summary",
                "done",
                "--channel",
                "terminal",
                "--confirm",
                env={"AI_DEVKIT_CONFIG_HOME": tmpdir},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "sent")
        self.assertEqual(payload["channel"], "terminal")

    def test_configure_runner_configures_terminal_channel(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_python(
                CONFIGURE_RUNNER,
                "--channel",
                "terminal",
                "--enabled",
                "true",
                "--event-filter",
                "task.completed",
                env={"AI_DEVKIT_CONFIG_HOME": tmpdir},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "configured")
        self.assertEqual(payload["channel"], "terminal")
        self.assertTrue(payload["channel_config"]["enabled"])


if __name__ == "__main__":
    unittest.main()
