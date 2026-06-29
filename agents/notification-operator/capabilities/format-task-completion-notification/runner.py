#!/usr/bin/env python3
"""Runner for notification-operator/format-task-completion-notification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from cli.aikit.notifications import format_notification_event  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Format a canonical task notification")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--event", default="task.completed")
    parser.add_argument("--status")
    parser.add_argument("--task-id")
    parser.add_argument("--title", default="Agent DevKit")
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--next-step", action="append", default=[])
    parser.add_argument("--severity", default="info")
    parser.add_argument("--sensitive", action="store_true")
    args = parser.parse_args()
    result = format_notification_event(
        {
            "event": args.event,
            "status": args.status,
            "task_id": args.task_id,
            "title": args.title,
            "summary": args.summary,
            "artifacts": args.artifact,
            "next_steps": args.next_step,
            "severity": args.severity,
            "sensitive": args.sensitive,
            "origin": "core",
        }
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
