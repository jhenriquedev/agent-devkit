#!/usr/bin/env python3
"""Shared helpers for AWS CloudWatch Log Analyzer capability runners."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from html import unescape
from pathlib import Path
from typing import Any


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
CLOUDWATCH_DIR = AGENT_DIR / "infra" / "integrations" / "aws-cloudwatch"


def load_fixture(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_repository() -> Any:
    sys.path.insert(0, str(CLOUDWATCH_DIR))
    from cloudwatch_repository import CloudWatchRepository  # pylint: disable=import-error

    return CloudWatchRepository()


def write_output(markdown: str, output: str | None) -> None:
    if output:
        Path(output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(unescape(text).split())


def value_or_dash(value: Any) -> str:
    text = clean_text(value)
    return text if text else "-"


def summarize(value: Any, limit: int = 500) -> str:
    text = clean_text(value)
    if not text:
        return "-"
    return text[:limit] + ("..." if len(text) > limit else "")


def get_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "events" in payload:
        return payload.get("events") or []
    if "log_events" in payload:
        return payload.get("log_events") or []
    return []


def event_message(event: dict[str, Any]) -> str:
    return clean_text(event.get("message"))


def is_error_event(event: dict[str, Any]) -> bool:
    message = event_message(event).lower()
    return any(token in message for token in ("error", "exception", "fatal", "fail", "warning"))


def sort_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(events, key=lambda item: item.get("timestamp") or 0)


def group_by_message(events: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for event in events:
        counter[normalize_message(event_message(event))] += 1
    return counter


def normalize_message(message: str) -> str:
    text = re.sub(r"\b[0-9a-f]{8,}\b", "<id>", message.lower())
    text = re.sub(r"\b\d+\b", "<number>", text)
    return text[:140] or "-"


def extract_status_code(message: str) -> str:
    match = re.search(r"\b([1-5][0-9]{2})\b", message)
    return match.group(1) if match else "-"


def extract_endpoint(message: str) -> str:
    match = re.search(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[^\s\"']+)", message)
    return f"{match.group(1)} {match.group(2)}" if match else "-"


def render_events_table(events: list[dict[str, Any]], limit: int = 10) -> list[str]:
    lines = [
        "| Timestamp | Stream | Message |",
        "|---|---|---|",
    ]
    for event in events[:limit]:
        lines.append(
            "| "
            + " | ".join(
                [
                    value_or_dash(event.get("timestamp")),
                    value_or_dash(event.get("log_stream_name")),
                    summarize(event.get("message"), 220),
                ]
            )
            + " |"
        )
    if not events:
        lines.append("| - | - | Nenhum evento encontrado |")
    return lines


def render_counter(counter: Counter[str], limit: int = 10) -> list[str]:
    if not counter:
        return ["- Nenhum item."]
    return [f"- {key}: {count}" for key, count in counter.most_common(limit)]


def require_event_scope(args: Any) -> None:
    missing = [
        name
        for name in ("region", "log_group", "start_time", "end_time")
        if not getattr(args, name, None)
    ]
    if missing and not getattr(args, "fixture", None):
        raise ValueError(f"missing required scope: {', '.join(missing)}")


def load_events_payload(args: Any) -> dict[str, Any]:
    if getattr(args, "fixture", None):
        return load_fixture(args.fixture)
    require_event_scope(args)
    repo = get_repository()
    return repo.filter_log_events(
        region=args.region,
        log_group=args.log_group,
        start_time=args.start_time,
        end_time=args.end_time,
        filter_pattern=getattr(args, "filter_pattern", None),
        log_stream_prefix=getattr(args, "log_stream_prefix", None),
        limit=getattr(args, "limit", 100),
    )


def print_error(exc: Exception) -> int:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1
