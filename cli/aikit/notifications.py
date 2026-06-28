"""Notification payload helpers for local automations."""

from __future__ import annotations

from typing import Any


def terminal_notification(message: str) -> dict[str, Any]:
    return {"type": "terminal", "message": message}
