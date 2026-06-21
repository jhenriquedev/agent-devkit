#!/usr/bin/env python3
"""Shared helpers for Elasticsearch Log Analyzer runners."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
ELASTICSEARCH_DIR = AGENT_DIR / "infra" / "integrations" / "elasticsearch"


def load_fixture(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_repository() -> Any:
    sys.path.insert(0, str(ELASTICSEARCH_DIR))
    from elasticsearch_repository import ElasticsearchRepository  # pylint: disable=import-error

    return ElasticsearchRepository()


def write_output(markdown: str, output: str | None) -> None:
    if output:
        Path(output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)


def print_error(exc: Exception) -> int:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1


def value_or_dash(value: Any) -> str:
    if value is None:
        return "-"
    text = " ".join(str(value).replace("\r", " ").replace("\n", " ").split())
    return text if text else "-"


def parse_filters(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    return json.loads(raw)


def search_kwargs(args: Any) -> dict[str, Any]:
    return {
        "source": args.source,
        "start_time": args.start_time,
        "end_time": args.end_time,
        "query_text": args.query,
        "service": args.service,
        "environment": args.environment,
        "level": args.level,
        "filters": parse_filters(args.filters_json),
        "time_field": args.time_field,
        "limit": args.limit,
    }


def event_rows(events: list[dict[str, Any]], limit: int = 20) -> list[str]:
    if not events:
        return ["| - | - | - | - | - | - |"]
    rows = ["| Time | Service | Level | Trace | Message | ID |", "|---|---|---|---|---|---|"]
    for event in events[:limit]:
        rows.append(
            "| "
            + " | ".join(
                [
                    value_or_dash(event.get("timestamp")),
                    value_or_dash(event.get("service")),
                    value_or_dash(event.get("level")),
                    value_or_dash(event.get("trace_id")),
                    truncate(value_or_dash(event.get("message")), 180),
                    value_or_dash(event.get("id")),
                ]
            )
            + " |"
        )
    return rows


def render_buckets(buckets: list[dict[str, Any]], key_name: str = "key") -> list[str]:
    if not buckets:
        return ["- No bucket."]
    return [f"- {value_or_dash(bucket.get(key_name))}: {value_or_dash(bucket.get('doc_count'))}" for bucket in buckets]


def fingerprint(message: Any) -> str:
    text = value_or_dash(message).lower()
    text = re.sub(r"\b[0-9a-f]{8,}\b", "<hex>", text)
    text = re.sub(r"\b\d+\b", "<num>", text)
    return truncate(text, 160)


def count_patterns(events: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for event in events:
        counter[fingerprint(event.get("message"))] += 1
    return counter


def render_counter(counter: Counter[str], limit: int = 10) -> list[str]:
    if not counter:
        return ["- No pattern."]
    return [f"- {key}: {count}" for key, count in counter.most_common(limit)]


def truncate(value: str, limit: int) -> str:
    return value[:limit] + ("..." if len(value) > limit else "")


def fixture_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return payload.get("events") or payload.get("items") or []
