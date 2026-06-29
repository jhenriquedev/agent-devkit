#!/usr/bin/env python3
"""Runner for notification-operator/send-task-completion-notification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from cli.aikit.notifications import send_notification  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a canonical task notification")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--event", default="task.completed")
    parser.add_argument("--status")
    parser.add_argument("--task-id")
    parser.add_argument("--title", default="Agent DevKit")
    parser.add_argument("--channel", action="append", default=[])
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--next-step", action="append", default=[])
    parser.add_argument("--severity", default="info")
    parser.add_argument("--sensitive", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    if not args.confirm:
        print(
            json.dumps(
                {
                    "kind": "task-notification-send",
                    "status": "needs-confirmation",
                    "ok": False,
                    "message": "Sending notifications requires --confirm.",
                    "write_policy": "confirm",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    result = send_notification(
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
        },
        force=True,
        channels=args.channel or ["desktop"],
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") is not False else 1


if __name__ == "__main__":
    raise SystemExit(main())
