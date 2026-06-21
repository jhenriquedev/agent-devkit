#!/usr/bin/env python3
"""Tests for CloudWatchRepository helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


AWS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AWS_DIR))

from cloudwatch_repository import CloudWatchConfig, CloudWatchRepository, to_epoch_ms  # noqa: E402


class CloudWatchRepositoryTest(unittest.TestCase):
    def test_normalizes_log_event(self) -> None:
        normalized = CloudWatchRepository._normalize_log_event(
            {
                "timestamp": 1,
                "ingestionTime": 2,
                "logStreamName": "stream",
                "message": "hello",
                "eventId": "abc",
            }
        )

        self.assertEqual(normalized["log_stream_name"], "stream")
        self.assertEqual(normalized["ingestion_time"], 2)

    def test_config_allows_default_region(self) -> None:
        config = CloudWatchConfig(default_region="us-east-1", profile="dev")

        self.assertEqual(config.default_region, "us-east-1")
        self.assertEqual(config.profile, "dev")

    def test_parses_iso_datetime_to_epoch_ms(self) -> None:
        self.assertEqual(to_epoch_ms("1970-01-01T00:00:01Z"), 1000)


if __name__ == "__main__":
    unittest.main()
