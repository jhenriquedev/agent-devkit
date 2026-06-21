#!/usr/bin/env python3
"""Tests for Elasticsearch repository helpers."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ELASTICSEARCH_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ELASTICSEARCH_DIR))

from elasticsearch_repository import (  # noqa: E402
    ElasticsearchConfig,
    build_search_body,
    normalize_event,
    quote_source,
)


class ElasticsearchRepositoryTest(unittest.TestCase):
    def test_config_reads_api_key_aliases(self) -> None:
        with patch("elasticsearch_repository.load_dotenv", lambda: None), patch.dict(
            os.environ,
            {
                "ELASTICSEARCH_URL": "https://elastic.example.com",
                "EC_API_KEY": "secret",
            },
            clear=True,
        ):
            config = ElasticsearchConfig.from_env()

        self.assertEqual(config.base_url, "https://elastic.example.com")
        self.assertEqual(config.api_key, "secret")

    def test_quote_source_preserves_wildcards(self) -> None:
        self.assertEqual(quote_source("logs-prod-*"), "logs-prod-*")

    def test_build_search_body_uses_runtime_scope(self) -> None:
        body = build_search_body(
            start_time="now-2h",
            end_time="now",
            time_field="@timestamp",
            query_text="timeout",
            service="checkout-api",
            environment="prod",
            level="error",
            filters={"host.name": "app-01"},
            limit=25,
        )

        self.assertEqual(body["size"], 25)
        filters = body["query"]["bool"]["filter"]
        self.assertIn({"range": {"@timestamp": {"gte": "now-2h", "lte": "now"}}}, filters)
        self.assertIn({"query_string": {"query": "timeout", "default_operator": "AND"}}, filters)
        self.assertIn({"term": {"host.name": "app-01"}}, filters)

    def test_normalizes_nested_event(self) -> None:
        normalized = normalize_event(
            {
                "_id": "abc",
                "_index": "logs-prod",
                "_source": {
                    "@timestamp": "2026-06-21T10:00:00Z",
                    "service": {"name": "checkout-api"},
                    "log": {"level": "error"},
                    "trace": {"id": "trace-1"},
                    "message": "Timeout calling payment",
                },
            }
        )

        self.assertEqual(normalized["id"], "abc")
        self.assertEqual(normalized["service"], "checkout-api")
        self.assertEqual(normalized["level"], "error")
        self.assertEqual(normalized["trace_id"], "trace-1")


if __name__ == "__main__":
    unittest.main()
