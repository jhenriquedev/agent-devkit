"""Local scheduler entrypoints for Agent DevKit."""

from __future__ import annotations

from cli.aikit.tasks import scheduler_run_once


def run_scheduler_once(*, dry_run: bool = False) -> dict:
    return scheduler_run_once(dry_run=dry_run)


def scheduler_daemon_plan() -> dict:
    return {
        "kind": "scheduler",
        "status": "planned",
        "daemon": True,
        "message": "Scheduler daemon is not started by the MVP CLI. Use `agent scheduler run-once` from cron/systemd/launchd.",
    }
