#!/usr/bin/env python3
"""AWS CloudWatch Logs repository backed by the AWS CLI."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CloudWatchRepositoryError(RuntimeError):
    """Raised when AWS CLI calls fail or scope is invalid."""


@dataclass(frozen=True)
class CloudWatchConfig:
    default_region: str | None = None
    profile: str | None = None

    @classmethod
    def from_env(cls) -> "CloudWatchConfig":
        load_dotenv()
        return cls(
            default_region=os.environ.get("AWS_REGION") or None,
            profile=os.environ.get("AWS_PROFILE") or None,
        )


class CloudWatchRepository:
    """Small read-only repository for AWS CloudWatch Logs."""

    def __init__(self, config: CloudWatchConfig | None = None) -> None:
        self.config = config or CloudWatchConfig.from_env()

    def list_log_groups(
        self,
        *,
        region: str | None = None,
        log_group_prefix: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        resolved_region = self._resolve_region(region)
        command = [
            "logs",
            "describe-log-groups",
            "--region",
            resolved_region,
            "--limit",
            str(limit),
        ]
        if log_group_prefix:
            command.extend(["--log-group-name-prefix", log_group_prefix])

        result = self._aws(command)
        groups = result.get("logGroups", [])
        return {
            "region": resolved_region,
            "count": len(groups),
            "log_groups": [self._normalize_log_group(item) for item in groups],
        }

    def filter_log_events(
        self,
        *,
        region: str | None = None,
        log_group: str,
        start_time: str,
        end_time: str,
        filter_pattern: str | None = None,
        log_stream_prefix: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        resolved_region = self._resolve_region(region)
        if not log_group:
            raise CloudWatchRepositoryError("log_group is required")
        command = [
            "logs",
            "filter-log-events",
            "--region",
            resolved_region,
            "--log-group-name",
            log_group,
            "--start-time",
            str(to_epoch_ms(start_time)),
            "--end-time",
            str(to_epoch_ms(end_time)),
            "--limit",
            str(limit),
        ]
        if filter_pattern:
            command.extend(["--filter-pattern", filter_pattern])
        if log_stream_prefix:
            command.extend(["--log-stream-name-prefix", log_stream_prefix])

        result = self._aws(command)
        events = result.get("events", [])
        return {
            "region": resolved_region,
            "log_group": log_group,
            "start_time": start_time,
            "end_time": end_time,
            "filter_pattern": filter_pattern,
            "count": len(events),
            "events": [self._normalize_log_event(item) for item in events],
            "next_token": result.get("nextToken"),
        }

    def start_logs_insights_query(
        self,
        *,
        region: str | None = None,
        log_group: str,
        start_time: str,
        end_time: str,
        query: str,
        limit: int = 100,
    ) -> dict[str, Any]:
        resolved_region = self._resolve_region(region)
        command = [
            "logs",
            "start-query",
            "--region",
            resolved_region,
            "--log-group-name",
            log_group,
            "--start-time",
            str(to_epoch_seconds(start_time)),
            "--end-time",
            str(to_epoch_seconds(end_time)),
            "--query-string",
            query,
            "--limit",
            str(limit),
        ]
        return self._aws(command)

    def get_logs_insights_query_results(
        self,
        *,
        region: str | None = None,
        query_id: str,
    ) -> dict[str, Any]:
        resolved_region = self._resolve_region(region)
        result = self._aws(
            [
                "logs",
                "get-query-results",
                "--region",
                resolved_region,
                "--query-id",
                query_id,
            ]
        )
        return {
            "region": resolved_region,
            "query_id": query_id,
            "status": result.get("status"),
            "results": result.get("results", []),
            "statistics": result.get("statistics", {}),
        }

    def describe_log_streams(
        self,
        *,
        region: str | None = None,
        log_group: str,
        log_stream_prefix: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        resolved_region = self._resolve_region(region)
        command = [
            "logs",
            "describe-log-streams",
            "--region",
            resolved_region,
            "--log-group-name",
            log_group,
            "--limit",
            str(limit),
        ]
        if log_stream_prefix:
            command.extend(["--log-stream-name-prefix", log_stream_prefix])
        result = self._aws(command)
        return {
            "region": resolved_region,
            "log_group": log_group,
            "count": len(result.get("logStreams", [])),
            "log_streams": result.get("logStreams", []),
        }

    def _resolve_region(self, region: str | None) -> str:
        resolved = region or self.config.default_region
        if not resolved:
            raise CloudWatchRepositoryError("region is required")
        return resolved

    def _aws(self, args: list[str]) -> dict[str, Any]:
        command = ["aws", *args, "--output", "json"]
        if self.config.profile:
            command.extend(["--profile", self.config.profile])
        result = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            raise CloudWatchRepositoryError(result.stderr.strip() or "aws cli failed")
        try:
            return json.loads(result.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise CloudWatchRepositoryError(f"invalid aws cli json: {exc}") from exc

    @staticmethod
    def _normalize_log_group(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "log_group_name": item.get("logGroupName"),
            "creation_time": item.get("creationTime"),
            "retention_in_days": item.get("retentionInDays"),
            "metric_filter_count": item.get("metricFilterCount"),
            "stored_bytes": item.get("storedBytes"),
            "arn": item.get("arn"),
        }

    @staticmethod
    def _normalize_log_event(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "timestamp": item.get("timestamp"),
            "ingestion_time": item.get("ingestionTime"),
            "log_stream_name": item.get("logStreamName"),
            "message": item.get("message"),
            "event_id": item.get("eventId"),
        }


def to_epoch_ms(value: str) -> int:
    return int(to_datetime(value).timestamp() * 1000)


def to_epoch_seconds(value: str) -> int:
    return int(to_datetime(value).timestamp())


def to_datetime(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise CloudWatchRepositoryError(f"invalid datetime: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def load_dotenv() -> None:
    for candidate in _dotenv_candidates():
        if not candidate.exists():
            continue
        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        return


def _dotenv_candidates() -> list[Path]:
    paths = []
    for start in (Path.cwd(), Path(__file__).resolve()):
        current = start if start.is_dir() else start.parent
        paths.extend(parent / ".env" for parent in [current, *current.parents])
    seen = set()
    unique = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique
