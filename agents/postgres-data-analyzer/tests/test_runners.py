#!/usr/bin/env python3
"""Smoke tests for Postgres Data Analyzer runners through ai-devkit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


class PostgresRunnerSmokeTest(unittest.TestCase):
    def test_connection_from_fixture(self) -> None:
        result = run_capability(
            "test-connection",
            {"database": "app", "user_name": "readonly", "current_schema": "public", "version": "PostgreSQL 16"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Connection", result.stdout)
        self.assertIn("database: app", result.stdout)

    def test_list_schemas_from_fixture(self) -> None:
        result = run_capability("list-schemas", {"schemas": [{"schema_name": "public"}]})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Schemas", result.stdout)
        self.assertIn("public", result.stdout)

    def test_list_tables_from_fixture(self) -> None:
        result = run_capability(
            "list-tables",
            {"schema": "public", "tables": [{"table_schema": "public", "table_name": "customers", "table_type": "BASE TABLE"}]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Tables", result.stdout)
        self.assertIn("customers", result.stdout)

    def test_database_override_is_rendered_from_fixture(self) -> None:
        result = run_capability(
            "list-tables",
            {"schema": "public", "tables": []},
            ["--database", "other_db"],
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("- Database: other_db", result.stdout)

    def test_describe_table_from_fixture(self) -> None:
        result = run_capability(
            "describe-table",
            {
                "schema": "public",
                "table": "customers",
                "columns": [{"column_name": "cpf", "data_type": "text", "is_nullable": "YES", "column_default": None}],
                "indexes": [{"indexname": "customers_pkey", "indexdef": "create unique index"}],
                "constraints": [{"constraint_name": "customers_pkey", "constraint_type": "PRIMARY KEY"}],
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Table Description", result.stdout)
        self.assertIn("cpf", result.stdout)

    def test_run_readonly_query_masks_cpf(self) -> None:
        result = run_capability("run-readonly-query", {"row_count": 1, "limit": 100, "rows": [{"cpf": "12345678909", "name": "Ana"}]})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("123.***.***-09", result.stdout)

    def test_profile_table_from_fixture(self) -> None:
        result = run_capability(
            "profile-table",
            {
                "schema": "public",
                "table": "customers",
                "row_count": 10,
                "columns": [{"column_name": "cpf", "data_type": "text", "total_rows": 10, "null_count": 1, "distinct_count": 9}],
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Table Profile", result.stdout)
        self.assertIn("Row count: 10", result.stdout)

    def test_detect_sensitive_columns_from_fixture(self) -> None:
        result = run_capability(
            "detect-sensitive-columns",
            {"columns": [{"table_schema": "public", "table_name": "customers", "column_name": "cpf", "data_type": "text", "sensitive_kind": "cpf"}]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Sensitive Columns", result.stdout)
        self.assertIn("cpf", result.stdout)

    def test_analyze_cpf_column_from_fixture(self) -> None:
        result = run_capability(
            "analyze-cpf-column",
            {
                "schema": "public",
                "table": "customers",
                "column": "cpf",
                "total_rows": 10,
                "blank_count": 1,
                "invalid_format_count": 2,
                "repeated_digits_count": 1,
                "valid_count": 5,
                "invalid_check_digit_count": 1,
                "duplicated_document_count": 1,
                "duplicated_row_count": 2,
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres CPF Analysis", result.stdout)
        self.assertIn("valid_count: 5", result.stdout)

    def test_generate_data_report_from_fixture(self) -> None:
        result = run_capability(
            "generate-data-report",
            {
                "profile": {
                    "schema": "public",
                    "table": "customers",
                    "row_count": 10,
                    "columns": [{"column_name": "cpf", "data_type": "text", "total_rows": 10, "null_count": 8, "distinct_count": 2}],
                },
                "sensitive": {
                    "columns": [{"table_schema": "public", "table_name": "customers", "column_name": "cpf", "data_type": "text", "sensitive_kind": "cpf"}]
                },
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Data Report", result.stdout)
        self.assertIn("Sensitive Columns", result.stdout)

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
        self.assertIn("# Postgres Join Suggestions", result.stdout)
        self.assertIn("sales.orders", result.stdout)
        self.assertIn("crm.customers", result.stdout)

    def test_generate_erd_report_from_fixture(self) -> None:
        result = run_capability(
            "generate-erd-report",
            {
                "relationships": [
                    {
                        "relationship_name": "orders_customer_id_fkey",
                        "parent_table": "sales.orders",
                        "parent_column": "customer_id",
                        "referenced_table": "crm.customers",
                        "referenced_column": "id",
                    }
                ]
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres ERD Report", result.stdout)
        self.assertIn("erDiagram", result.stdout)

    def test_validate_readonly_query_blocks_write_without_connection(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "run",
                "postgres-data-analyzer",
                "validate-readonly-query",
                "--query",
                "delete from public.users",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("blocked SQL keyword", result.stderr)


def run_capability(capability: str, fixture: dict, extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = Path(tmpdir) / "fixture.json"
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(CLI),
                "run",
                "postgres-data-analyzer",
                capability,
                *(extra_args or []),
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
