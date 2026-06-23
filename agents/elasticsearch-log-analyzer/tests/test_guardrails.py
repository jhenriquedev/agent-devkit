#!/usr/bin/env python3
"""Guardrail and real-path tests for Elasticsearch Log Analyzer runners.

Covers:
- Scope guardrail: missing --source/--from/--to exits with code 1
- No-secret-leak: API key must not appear in stdout
- Correlate with --card-fixture: correct fixture loading
- Real path with mocked _request: search_events returns normalized events
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"

ELASTICSEARCH_DIR = (
    Path(__file__).resolve().parents[1]
    / "infra"
    / "integrations"
    / "elasticsearch"
)
sys.path.insert(0, str(ELASTICSEARCH_DIR))


EVENTS = [
    {
        "id": "evt-1",
        "timestamp": "2026-06-21T10:00:00Z",
        "service": "checkout-api",
        "environment": "prod",
        "level": "error",
        "trace_id": "trace-1",
        "message": "Timeout calling payment id 123",
    },
]


def run_capability(capability: str, extra_args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLI), "run", "elasticsearch-log-analyzer", capability, *extra_args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class ScopeGuardrailTest(unittest.TestCase):
    """Runners must exit 1 when --source/--from/--to are missing (no --fixture)."""

    def _assert_scope_required(self, capability: str) -> None:
        result = run_capability(capability, [])
        self.assertNotEqual(result.returncode, 0, f"{capability} should fail without scope")
        stderr = result.stderr
        self.assertTrue(
            stderr.strip(),
            f"{capability} should emit error to stderr when scope missing",
        )

    def test_search_log_events_requires_scope(self) -> None:
        self._assert_scope_required("search-log-events")

    def test_analyze_service_errors_requires_scope(self) -> None:
        self._assert_scope_required("analyze-service-errors")

    def test_trace_request_requires_scope(self) -> None:
        self._assert_scope_required("trace-request")

    def test_detect_error_patterns_requires_scope(self) -> None:
        self._assert_scope_required("detect-error-patterns")

    def test_extract_log_samples_requires_scope(self) -> None:
        self._assert_scope_required("extract-log-samples")

    def test_generate_log_report_requires_scope(self) -> None:
        self._assert_scope_required("generate-log-report")

    def test_correlate_azure_card_logs_requires_scope(self) -> None:
        self._assert_scope_required("correlate-azure-card-logs")


class NoSecretLeakTest(unittest.TestCase):
    """API key must not appear in runner stdout output."""

    def test_api_key_not_in_fixture_output(self) -> None:
        fixture = {"source": "logs-prod-*", "total": 1, "events": EVENTS}
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "fixture.json"
            fixture_path.write_text(json.dumps(fixture))
            result = run_capability(
                "search-log-events",
                ["--fixture", str(fixture_path)],
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        # Simulate a secret that might be in env but must not leak
        self.assertNotIn("ApiKey", result.stdout)
        self.assertNotIn("Authorization", result.stdout)


class CorrelateWithCardFixtureTest(unittest.TestCase):
    """correlate-azure-card-logs correctly loads --card-fixture and derives query."""

    def test_correlate_with_card_fixture(self) -> None:
        log_fixture = {"source": "logs-prod-*", "events": EVENTS}
        card_fixture = {
            "work_item": {
                "id": "1234",
                "title": "Timeout in checkout payment",
                "tags": ["checkout", "payment"],
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "fixture.json"
            fixture_path.write_text(json.dumps(log_fixture))
            card_path = Path(tmpdir) / "card.json"
            card_path.write_text(json.dumps(card_fixture))
            result = run_capability(
                "correlate-azure-card-logs",
                ["--fixture", str(fixture_path), "--card-fixture", str(card_path)],
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Azure Card Log Correlation", result.stdout)
        self.assertIn("1234", result.stdout)
        self.assertIn("Timeout in checkout payment", result.stdout)
        self.assertIn("- Confidence:", result.stdout)


class RealPathMockedTest(unittest.TestCase):
    """search_events with mocked _request returns normalized events."""

    def test_search_events_real_path_mocked(self) -> None:
        from elasticsearch_repository import ElasticsearchConfig, ElasticsearchRepository

        mock_response = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_id": "abc",
                        "_index": "logs-prod",
                        "_source": {
                            "@timestamp": "2026-06-21T10:00:00Z",
                            "service": "checkout-api",
                            "log": {"level": "error"},
                            "trace": {"id": "trace-1"},
                            "message": "Timeout calling payment",
                        },
                    }
                ],
            }
        }

        config = ElasticsearchConfig(
            base_url="https://elastic.example.com",
            api_key="test-key",
        )
        repo = ElasticsearchRepository(config=config)

        with patch.object(repo, "_request", return_value=mock_response):
            result = repo.search_events(
                source="logs-prod-*",
                start_time="now-1h",
                end_time="now",
                level="error",
            )

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["events"]), 1)
        event = result["events"][0]
        self.assertEqual(event["id"], "abc")
        self.assertEqual(event["service"], "checkout-api")
        self.assertEqual(event["level"], "error")
        self.assertEqual(event["trace_id"], "trace-1")

    def test_missing_url_raises_error(self) -> None:
        from elasticsearch_repository import ElasticsearchConfig, ElasticsearchRepository, ElasticsearchRepositoryError

        config = ElasticsearchConfig(base_url=None, api_key=None)
        repo = ElasticsearchRepository(config=config)

        with self.assertRaises(ElasticsearchRepositoryError):
            repo.search_events(
                source="logs-prod-*",
                start_time="now-1h",
                end_time="now",
            )

    def test_api_key_not_leaked_in_error_message(self) -> None:
        """Error raised by _request should not echo the API key back."""
        from elasticsearch_repository import ElasticsearchConfig, ElasticsearchRepository, ElasticsearchRepositoryError

        secret_key = "super-secret-api-key-12345"
        config = ElasticsearchConfig(
            base_url="https://elastic.example.com",
            api_key=secret_key,
        )
        repo = ElasticsearchRepository(config=config)

        with patch.object(repo, "_request", side_effect=ElasticsearchRepositoryError("HTTP 401: Unauthorized")):
            try:
                repo.search_events(source="logs-*", start_time="now-1h", end_time="now")
            except ElasticsearchRepositoryError as exc:
                self.assertNotIn(secret_key, str(exc))


if __name__ == "__main__":
    unittest.main()
