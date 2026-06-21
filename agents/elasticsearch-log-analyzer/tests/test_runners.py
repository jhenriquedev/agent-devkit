#!/usr/bin/env python3
"""Smoke tests for Elasticsearch Log Analyzer runners through ai-devkit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


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
    {
        "id": "evt-2",
        "timestamp": "2026-06-21T10:01:00Z",
        "service": "checkout-api",
        "environment": "prod",
        "level": "error",
        "trace_id": "trace-1",
        "message": "Timeout calling payment id 456",
    },
]


class ElasticsearchRunnerSmokeTest(unittest.TestCase):
    def test_list_log_sources_from_fixture(self) -> None:
        fixture = {
            "pattern": "logs-*",
            "indices": [{"index": "logs-prod-000001"}],
            "data_streams": [{"name": "logs-prod"}],
            "aliases": [{"alias": "logs-current"}],
        }
        result = run_capability("list-log-sources", fixture)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Elasticsearch Log Sources", result.stdout)
        self.assertIn("logs-prod-000001", result.stdout)

    def test_search_log_events_from_fixture(self) -> None:
        result = run_capability("search-log-events", {"source": "logs-prod-*", "total": 2, "events": EVENTS})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Elasticsearch Log Events", result.stdout)
        self.assertIn("Timeout calling payment", result.stdout)

    def test_analyze_service_errors_from_fixture(self) -> None:
        result = run_capability("analyze-service-errors", {"source": "logs-prod-*", "events": EVENTS})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Elasticsearch Service Error Analysis", result.stdout)
        self.assertIn("timeout calling payment id <num>", result.stdout)

    def test_trace_request_from_fixture(self) -> None:
        result = run_capability("trace-request", {"source": "logs-prod-*", "request_id": "trace-1", "events": EVENTS})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Elasticsearch Request Trace", result.stdout)
        self.assertIn("trace-1", result.stdout)

    def test_detect_error_patterns_from_fixture(self) -> None:
        result = run_capability("detect-error-patterns", {"source": "logs-prod-*", "events": EVENTS})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Elasticsearch Error Patterns", result.stdout)
        self.assertIn("timeout calling payment id <num>", result.stdout)

    def test_extract_log_samples_from_fixture(self) -> None:
        result = run_capability("extract-log-samples", {"source": "logs-prod-*", "events": EVENTS})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Elasticsearch Log Samples", result.stdout)
        self.assertIn("evt-1", result.stdout)

    def test_generate_log_report_from_fixture(self) -> None:
        result = run_capability("generate-log-report", {"source": "logs-prod-*", "count": 2, "events": EVENTS})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Elasticsearch Log Report", result.stdout)
        self.assertIn("- Matching events: 2", result.stdout)

    def test_correlate_azure_card_logs_from_fixture(self) -> None:
        result = run_capability("correlate-azure-card-logs", {"source": "logs-prod-*", "events": EVENTS})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Azure Card Log Correlation", result.stdout)
        self.assertIn("- Confidence: medium", result.stdout)


def run_capability(capability: str, fixture: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = Path(tmpdir) / "fixture.json"
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(CLI),
                "run",
                "elasticsearch-log-analyzer",
                capability,
                "--fixture",
                str(fixture_path),
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


if __name__ == "__main__":
    unittest.main()
