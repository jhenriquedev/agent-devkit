#!/usr/bin/env python3
"""Tests for the SQL Server Data Analyzer agent."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "ai-devkit"
AGENT = "sqlserver-data-analyzer"


EXPECTED_CAPABILITIES = {
    "analyze-cpf-column",
    "analyze-query-result",
    "build-analysis-query",
    "compare-tables",
    "describe-table",
    "detect-data-quality-issues",
    "detect-sensitive-columns",
    "estimate-table-size",
    "explore-database-domain",
    "explain-query-plan",
    "generate-data-report",
    "generate-erd-report",
    "list-databases",
    "list-relationships",
    "list-schemas",
    "list-tables",
    "profile-table",
    "run-readonly-query",
    "sample-table",
    "search-columns",
    "search-tables",
    "suggest-joins",
    "test-connection",
    "trace-record",
    "validate-readonly-query",
}


class SqlServerDataAnalyzerCliTest(unittest.TestCase):
    def test_lists_all_capabilities(self) -> None:
        result = run_cli("--json", "capabilities", AGENT)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        capabilities = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertEqual(capabilities, EXPECTED_CAPABILITIES)

    def test_all_capabilities_have_runner(self) -> None:
        for capability in sorted(EXPECTED_CAPABILITIES):
            with self.subTest(capability=capability):
                result = run_cli("--json", "inspect", AGENT, capability)

                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                runner = payload["capability"]["entrypoint"]["runner"]
                self.assertTrue(runner["exists"])

    def test_run_readonly_query_masks_cpf_from_fixture(self) -> None:
        result = run_capability(
            "run-readonly-query",
            {"row_count": 1, "limit": 100, "rows": [{"cpf": "12345678909", "name": "Ana"}]},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# SQL Server Read-Only Query", result.stdout)
        self.assertIn("123.***.***-09", result.stdout)

    def test_run_readonly_query_can_render_json_from_fixture(self) -> None:
        result = run_capability(
            "run-readonly-query",
            {
                "row_count": 1,
                "limit": 100,
                "rows": [{"cpf": "12345678909", "name": "Ana", "api_key": "sk-prod-secret"}],
            },
            ["--format", "json"],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["row_count"], 1)
        self.assertEqual(payload["rows"][0]["cpf"], "123.***.***-09")
        self.assertEqual(payload["rows"][0]["api_key"], "***REDACTED***")
        self.assertNotIn("12345678909", result.stdout)
        self.assertNotIn("sk-prod-secret", result.stdout)

    def test_suggest_joins_from_fixture(self) -> None:
        result = run_capability(
            "suggest-joins",
            {
                "suggestions": [
                    {
                        "left_table": "sales.orders",
                        "left_column": "customer_id",
                        "right_table": "crm.customers",
                        "right_column": "id",
                        "confidence": "high",
                    }
                ]
            },
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# SQL Server Join Suggestions", result.stdout)
        self.assertIn("sales.orders", result.stdout)
        self.assertIn("crm.customers", result.stdout)

    def test_validate_readonly_query_blocks_write(self) -> None:
        result = run_cli("run", AGENT, "validate-readonly-query", "--query", "delete from dbo.users")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("blocked SQL keyword", result.stderr)


def run_capability(capability: str, fixture: dict, extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = Path(tmpdir) / "fixture.json"
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        return run_cli("run", AGENT, capability, *(extra_args or []), "--fixture", str(fixture_path))


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


if __name__ == "__main__":
    unittest.main()
