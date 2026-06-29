#!/usr/bin/env python3
"""Runner for notification-operator/configure-notification-channel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from cli.aikit.notifications import configure_notification_channel  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure a local notification channel")
    parser.add_argument("--channel", required=True)
    parser.add_argument("--enabled", choices=["true", "false"])
    parser.add_argument("--event-filter", action="append", default=[])
    args = parser.parse_args()
    enabled = None
    if args.enabled is not None:
        enabled = args.enabled == "true"
    result = configure_notification_channel(args.channel, enabled=enabled, events=args.event_filter or None)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") is not False else 1


if __name__ == "__main__":
    raise SystemExit(main())
