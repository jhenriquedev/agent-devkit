#!/usr/bin/env python3
"""CLI contracts for local notifications."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "agent"
CLI_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_CLI_TIMEOUT_SECONDS", "60"))


class NotificationsCliTest(unittest.TestCase):
    def run_agent(self, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(AGENT), *args],
            cwd=ROOT,
            env=os.environ | env,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CLI_TIMEOUT_SECONDS,
        )

    def test_notifications_list_events_and_configure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            events = self.run_agent("notifications", "list-events", "--json", env=env)
            channels = self.run_agent("notifications", "list-channels", "--json", env=env)
            configure = self.run_agent(
                "notifications",
                "configure",
                "--enabled",
                "true",
                "--event-filter",
                "task.completed",
                "--json",
                env=env,
            )
            configure_channel = self.run_agent(
                "notifications",
                "configure-channel",
                "--channel",
                "terminal",
                "--enabled",
                "true",
                "--event-filter",
                "task.completed",
                "--json",
                env=env,
            )

        self.assertEqual(events.returncode, 0, events.stderr)
        self.assertEqual(channels.returncode, 0, channels.stderr)
        self.assertEqual(configure.returncode, 0, configure.stderr)
        self.assertEqual(configure_channel.returncode, 0, configure_channel.stderr)
        self.assertIn("task.completed", json.loads(events.stdout)["events"])
        self.assertIn("terminal", {item["id"] for item in json.loads(channels.stdout)["channels"]})
        payload = json.loads(configure.stdout)
        self.assertTrue(payload["desktop"]["enabled"])
        self.assertEqual(payload["desktop"]["events"], ["task.completed"])
        channel_payload = json.loads(configure_channel.stdout)
        self.assertEqual(channel_payload["channel"], "terminal")
        self.assertTrue(channel_payload["channel_config"]["enabled"])

    def test_notifications_format_returns_canonical_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_agent(
                "notifications",
                "format",
                "--summary",
                "done",
                "--event",
                "task.completed",
                "--task-id",
                "daily-check",
                "--artifact",
                "report.md",
                "--json",
                env={"AI_DEVKIT_CONFIG_HOME": tmpdir},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "notification-event")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["task_id"], "daily-check")
        self.assertEqual(payload["artifacts"], ["report.md"])

    def test_notifications_send_requires_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_agent("notifications", "send", "--json", env={"AI_DEVKIT_CONFIG_HOME": tmpdir})

        self.assertEqual(result.returncode, 1)
        self.assertIn("requires --message", result.stderr)


if __name__ == "__main__":
    unittest.main()
