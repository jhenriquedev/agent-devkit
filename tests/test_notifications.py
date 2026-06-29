#!/usr/bin/env python3
"""Contracts for local desktop notifications."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cli.aikit.notifications import (
    configure_notification_channel,
    configure_notifications,
    format_notification_event,
    list_notification_channels,
    list_notification_events,
    notification_config,
    notification_doctor,
    notification_history_path,
    send_notification_command,
)
from cli.aikit.tasks import create_task, run_task, scheduler_run_once


UNAVAILABLE_BACKEND = {
    "platform": "linux",
    "name": "notify-send",
    "available": False,
    "status": "headless",
    "command": None,
    "reason": "desktop-session-unavailable",
}


class NotificationContractsTest(unittest.TestCase):
    def test_config_defaults_to_disabled_with_failure_events(self) -> None:
        with isolated_home():
            config = notification_config()

        self.assertFalse(config["desktop"]["enabled"])
        self.assertEqual(config["desktop"]["events"], ["task.failed", "task.blocked", "scheduled_task.failed", "scheduled_task.blocked"])

    def test_configure_notifications_persists_desktop_preferences(self) -> None:
        with isolated_home() as home:
            result = configure_notifications(enabled=True, events=["task.completed", "scheduled_task.completed"])
            config_path = Path(result["config_path"])
            config = notification_config()

        self.assertEqual(result["status"], "configured")
        self.assertEqual(config_path, home / "config.json")
        self.assertTrue(result["desktop"]["enabled"])
        self.assertEqual(result["desktop"]["events"], ["task.completed", "scheduled_task.completed"])
        self.assertEqual(config["channels"]["desktop"]["events"], ["task.completed", "scheduled_task.completed"])

    def test_configure_terminal_channel_persists_local_preferences(self) -> None:
        with isolated_home():
            result = configure_notification_channel("terminal", enabled=True, events=["task.completed"])
            config = notification_config()

        self.assertEqual(result["status"], "configured")
        self.assertEqual(result["channel"], "terminal")
        self.assertTrue(config["channels"]["terminal"]["enabled"])
        self.assertEqual(config["channels"]["terminal"]["events"], ["task.completed"])

    def test_format_notification_event_redacts_and_sets_status(self) -> None:
        result = format_notification_event(
            {
                "event": "artifact.generated",
                "summary": "created with token sk-1234567890abcd",
                "task_id": "build-report",
                "run_id": "run_123",
                "scheduled_for": "2026-06-28T10:00:00+00:00",
                "started_at": "2026-06-28T10:00:00+00:00",
                "finished_at": "2026-06-28T10:00:42+00:00",
                "duration_seconds": 42,
                "audit_id": "exec_123",
                "artifacts": ["report.md"],
                "next_steps": ["review report"],
            }
        )

        self.assertEqual(result["kind"], "notification-event")
        self.assertEqual(result["status"], "generated")
        self.assertEqual(result["task_id"], "build-report")
        self.assertEqual(result["run_id"], "run_123")
        self.assertEqual(result["duration_seconds"], 42)
        self.assertEqual(result["audit_id"], "exec_123")
        self.assertNotIn("sk-1234567890abcd", result["summary"])
        self.assertEqual(result["artifacts"], ["report.md"])

    def test_send_notification_command_is_best_effort_and_records_history(self) -> None:
        with isolated_home():
            with mock.patch("cli.aikit.notifications.detect_desktop_backend", return_value=UNAVAILABLE_BACKEND):
                result = send_notification_command(message="done with token sk-1234567890abcd")
            history = notification_history_path().read_text(encoding="utf-8")

        self.assertEqual(result["status"], "skipped")
        self.assertTrue(result["ok"])
        self.assertEqual(result["reason"], "desktop-session-unavailable")
        self.assertNotIn("sk-1234567890abcd", result["notification"]["message"])
        self.assertIn("desktop-session-unavailable", history)

    def test_available_backend_invokes_platform_command(self) -> None:
        backend = {
            "platform": "macos",
            "name": "osascript",
            "available": True,
            "status": "ok",
            "command": "/usr/bin/osascript",
            "reason": None,
        }
        process = mock.Mock(returncode=0, stdout="", stderr="")
        with isolated_home():
            with mock.patch("cli.aikit.notifications.detect_desktop_backend", return_value=backend), mock.patch(
                "cli.aikit.notifications.subprocess.run",
                return_value=process,
            ) as run:
                result = send_notification_command(message="done")

        self.assertEqual(result["status"], "sent")
        self.assertTrue(result["ok"])
        run.assert_called_once()

    def test_task_run_attaches_desktop_notification_without_failing_task(self) -> None:
        with isolated_home():
            create_task(
                task_id="notify-task",
                title="Notify task",
                notifications=[{"type": "desktop", "on": ["completed"]}],
            )
            with mock.patch("cli.aikit.notifications.detect_desktop_backend", return_value=UNAVAILABLE_BACKEND):
                result = run_task("notify-task")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["notification"]["status"], "skipped")
        self.assertEqual(result["notification"]["reason"], "desktop-session-unavailable")

    def test_scheduler_uses_scheduled_task_event_namespace(self) -> None:
        with isolated_home():
            create_task(
                task_id="scheduled-notify",
                title="Scheduled notify",
                schedule={"type": "interval", "every": "1m"},
                notifications=[{"type": "desktop", "on": ["completed"]}],
            )
            with mock.patch("cli.aikit.notifications.detect_desktop_backend", return_value=UNAVAILABLE_BACKEND):
                result = scheduler_run_once()
            event_lines = [line for line in Path(result["runs"][0]["events_path"]).read_text(encoding="utf-8").splitlines() if line]

        self.assertEqual(result["due_count"], 1)
        run = result["runs"][0]
        notification = run["notification"]
        self.assertRegex(run["run_id"], r"^run_")
        self.assertEqual(run["event"], "scheduled_task.completed")
        self.assertEqual(run["autonomy_contract"]["level_id"], "scheduled")
        self.assertEqual(run["preview"]["autonomy_contract"]["level"], 4)
        self.assertEqual(run["events"][1]["autonomy"]["level_id"], "scheduled")
        self.assertIn("audit_id", run)
        self.assertIsNotNone(run["duration_seconds"])
        self.assertEqual(len(event_lines), 2)
        self.assertIn('"event": "scheduled_task.started"', event_lines[0])
        self.assertIn('"event": "scheduled_task.completed"', event_lines[1])
        self.assertEqual(notification["notification"]["event"], "scheduled_task.completed")

    def test_scheduler_blocks_external_write_with_audit_and_notification_metadata(self) -> None:
        with isolated_home():
            create_task(
                task_id="scheduled-blocked",
                title="Scheduled blocked",
                schedule={"type": "interval", "every": "1m"},
                action={"type": "capability", "agent": "demo", "capability": "write", "external_writes": True},
                permissions={"mode": "report-only"},
                notify={"on": ["blocked"], "channels": ["terminal"]},
            )
            result = scheduler_run_once()

        run = result["runs"][0]
        self.assertEqual(run["status"], "blocked")
        self.assertEqual(run["event"], "scheduled_task.blocked")
        self.assertTrue(run["requires_permission"])
        self.assertIn("audit_id", run)
        self.assertEqual(run["notification"]["channel"], "terminal")
        self.assertEqual(run["notification"]["notification"]["run_id"], run["run_id"])

    def test_scheduler_failed_task_records_retry_scheduled_event(self) -> None:
        token = "sk-1234567890abcd"
        with isolated_home():
            create_task(
                task_id="scheduled-retry",
                title="Scheduled retry",
                schedule={"type": "interval", "every": "1m", "retry": {"max_attempts": 2, "delay": "5m"}},
                notify={"on": ["failure", "retry"], "channels": ["terminal"]},
            )
            with mock.patch("cli.aikit.tasks.save_tasks", side_effect=OSError(f"failed token {token}")):
                result = scheduler_run_once()
            events = Path(result["runs"][0]["events_path"]).read_text(encoding="utf-8")

        run = result["runs"][0]
        self.assertEqual(run["status"], "failed")
        self.assertEqual(run["event"], "scheduled_task.failed")
        self.assertNotIn(token, run["error"])
        self.assertEqual(run["retry"]["status"], "scheduled")
        self.assertEqual(run["retry"]["attempt"], 2)
        self.assertIn('"event": "scheduled_task.failed"', events)
        self.assertIn('"event": "scheduled_task.retry_scheduled"', events)

    def test_task_notify_contract_supports_terminal_channel(self) -> None:
        with isolated_home():
            create_task(
                task_id="notify-contract",
                title="Notify contract",
                notify={"on": ["completion"], "channels": ["terminal"]},
            )
            result = run_task("notify-contract")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["notification"]["status"], "sent")
        self.assertEqual(result["notification"]["channel"], "terminal")
        self.assertEqual(result["notification"]["notification"]["status"], "ok")

    def test_task_notify_contract_supports_multiple_local_channels(self) -> None:
        with isolated_home():
            create_task(
                task_id="notify-multi",
                title="Notify multi",
                notify={"on": ["completion"], "channels": ["terminal", "audit"]},
            )
            result = run_task("notify-multi")
            history = notification_history_path().read_text(encoding="utf-8")

        self.assertEqual(result["notification"]["status"], "sent")
        self.assertEqual([item["channel"] for item in result["notification"]["deliveries"]], ["terminal", "audit"])
        self.assertIn('"channel": "terminal"', history)
        self.assertIn('"channel": "audit"', history)

    def test_list_notification_events_exposes_supported_contract(self) -> None:
        result = list_notification_events()

        self.assertIn("task.completed", result["events"])
        self.assertIn("artifact.generated", result["events"])
        self.assertIn("scheduled_task.completed", result["events"])
        self.assertIn("scheduled_task.progress", result["events"])
        self.assertIn("scheduled_task.retry_scheduled", result["events"])
        self.assertIn("scheduled_task.skipped", result["events"])
        self.assertIn("action_required", result["severities"])

    def test_list_notification_channels_exposes_local_and_future_channels(self) -> None:
        result = list_notification_channels()

        channels = {item["id"]: item["status"] for item in result["channels"]}
        self.assertEqual(channels["desktop"], "supported")
        self.assertEqual(channels["terminal"], "supported")
        self.assertEqual(channels["teams"], "future")

    def test_doctor_reports_backend_and_history_path(self) -> None:
        with isolated_home():
            with mock.patch("cli.aikit.notifications.detect_desktop_backend", return_value=UNAVAILABLE_BACKEND):
                result = notification_doctor()

        self.assertEqual(result["action"], "doctor")
        self.assertEqual(result["desktop"]["backend"]["status"], "headless")
        self.assertTrue(result["history_path"].endswith("notifications.jsonl"))


class isolated_home:
    def __enter__(self) -> Path:
        self.tmp = tempfile.TemporaryDirectory()
        self.old_env = {
            "AGENT_DEVKIT_HOME": os.environ.get("AGENT_DEVKIT_HOME"),
            "AI_DEVKIT_CONFIG_HOME": os.environ.get("AI_DEVKIT_CONFIG_HOME"),
            "AIKIT_CONFIG_HOME": os.environ.get("AIKIT_CONFIG_HOME"),
        }
        os.environ.pop("AGENT_DEVKIT_HOME", None)
        os.environ.pop("AIKIT_CONFIG_HOME", None)
        os.environ["AI_DEVKIT_CONFIG_HOME"] = self.tmp.name
        return Path(self.tmp.name).resolve()

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        for name, value in self.old_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        self.tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
