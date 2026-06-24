#!/usr/bin/env python3
"""Tests for Elasticsearch repository helpers."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ELASTICSEARCH_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ELASTICSEARCH_DIR))

from elasticsearch_repository import (  # noqa: E402
    ElasticsearchConfig,
    ElasticsearchRepository,
    build_search_body,
    load_dotenv,
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
        self.assertFalse(config.cloud_proxy)

    def test_config_derives_cloud_proxy_url_from_services_monitor_env(self) -> None:
        with patch("elasticsearch_repository.load_dotenv", lambda: None), patch.dict(
            os.environ,
            {
                "ELASTICSEARCH_CLOUD_PROXY": "true",
                "ELASTICSEARCH_CLOUD_API_BASE_URL": "https://api.elastic-cloud.com/",
                "ELASTICSEARCH_CLOUD_DEPLOYMENT_ID": "deployment-123",
                "ELASTICSEARCH_CLOUD_RESOURCE_REF_ID": "main-elasticsearch",
                "EC_API_KEY": "secret",
            },
            clear=True,
        ):
            config = ElasticsearchConfig.from_env()

        self.assertEqual(
            config.base_url,
            "https://api.elastic-cloud.com/api/v1/deployments/deployment-123/elasticsearch/main-elasticsearch/proxy",
        )
        self.assertTrue(config.cloud_proxy)

    def test_config_prefers_local_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, patch.dict(os.environ, {}, clear=True):
            root = Path(tmpdir)
            (root / ".env").write_text(
                "ELASTICSEARCH_URL=https://from-env.example.com\n"
                "ELASTICSEARCH_API_KEY=from-env\n",
                encoding="utf-8",
            )
            (root / ".env.local").write_text(
                "ELASTICSEARCH_URL=https://from-local.example.com\n"
                "ELASTICSEARCH_API_KEY=from-local\n",
                encoding="utf-8",
            )

            with patch("pathlib.Path.cwd", return_value=root):
                load_dotenv()

            self.assertEqual(os.environ["ELASTICSEARCH_URL"], "https://from-local.example.com")
            self.assertEqual(os.environ["ELASTICSEARCH_API_KEY"], "from-local")

    def test_request_does_not_pass_api_key_in_curl_argv(self) -> None:
        secret = "local-elastic-secret"
        config = ElasticsearchConfig(
            base_url="https://elastic.example.com",
            api_key=secret,
            cloud_proxy=True,
        )
        repo = ElasticsearchRepository(config=config)
        captured_command: list[str] = []
        captured_timeout: list[int | None] = []
        captured_curl_config: list[str] = []

        def fake_run(command: list[str], **_: object) -> object:
            captured_command[:] = command
            captured_timeout[:] = [_.get("timeout")]  # type: ignore[list-item]
            captured_curl_config[:] = [Path(command[command.index("--config") + 1]).read_text(encoding="utf-8")]
            response_path = Path(command[command.index("-o") + 1])
            response_path.write_text("{}", encoding="utf-8")
            return type("Completed", (), {"returncode": 0, "stdout": "200", "stderr": ""})()

        with patch("subprocess.run", side_effect=fake_run):
            repo.list_sources(pattern="logs-*")

        self.assertNotIn(secret, captured_command)
        self.assertIn("--config", captured_command)
        self.assertIn("-H", captured_command)
        self.assertIn("X-Management-Request: true", captured_command)
        self.assertIn("--max-time", captured_command)
        self.assertEqual(captured_command[captured_command.index("--max-time") + 1], "30")
        self.assertEqual(captured_timeout[0], 35)
        self.assertIn("Authorization: ApiKey local-elastic-secret", captured_curl_config[0])

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
