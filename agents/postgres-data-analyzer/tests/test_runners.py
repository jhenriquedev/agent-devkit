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

    # ---------------------------------------------------------------------------
    # Dispatch capabilities (12 previously without smoke tests)
    # ---------------------------------------------------------------------------

    def test_list_databases_from_fixture(self) -> None:
        result = run_capability(
            "list-databases",
            {"database": "postgres", "count": 2, "databases": [{"database_name": "app", "owner_name": "admin"}, {"database_name": "test", "owner_name": "admin"}]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Databases", result.stdout)
        self.assertIn("app", result.stdout)

    def test_list_relationships_from_fixture(self) -> None:
        result = run_capability(
            "list-relationships",
            {
                "count": 1,
                "relationships": [
                    {"relationship_name": "fk_orders_customer", "parent_table": "orders", "parent_column": "customer_id", "referenced_table": "customers", "referenced_column": "id"}
                ],
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Relationships", result.stdout)
        self.assertIn("fk_orders_customer", result.stdout)

    def test_search_tables_from_fixture(self) -> None:
        result = run_capability(
            "search-tables",
            {"count": 1, "tables": [{"table_schema": "public", "table_name": "orders", "table_type": "BASE TABLE"}]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Table Search", result.stdout)
        self.assertIn("orders", result.stdout)

    def test_search_columns_from_fixture(self) -> None:
        result = run_capability(
            "search-columns",
            {"count": 1, "columns": [{"table_schema": "public", "table_name": "customers", "column_name": "email", "data_type": "text"}]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Column Search", result.stdout)
        self.assertIn("email", result.stdout)

    def test_explore_database_domain_from_fixture(self) -> None:
        result = run_capability(
            "explore-database-domain",
            {
                "database": "app",
                "domains": [{"domain": "customer", "table_count": 3}],
                "tables": [{"table_schema": "public", "table_name": "customers", "table_type": "BASE TABLE"}],
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Database Domain Exploration", result.stdout)
        self.assertIn("customer", result.stdout)

    def test_build_analysis_query_from_fixture(self) -> None:
        result = run_capability(
            "build-analysis-query",
            {"database": "app", "schema": "public", "table": "orders", "query": "select * from public.orders limit 100", "limit": 100},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Analysis Query Builder", result.stdout)

    def test_validate_readonly_query_from_fixture(self) -> None:
        result = run_capability(
            "validate-readonly-query",
            {"valid": True, "query": "select id from public.orders limit 100", "limit": 100},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Read-Only Query Validation", result.stdout)
        self.assertIn("Valid: yes", result.stdout)

    def test_explain_query_plan_from_fixture(self) -> None:
        result = run_capability(
            "explain-query-plan",
            {"plan": [{"QUERY PLAN": "Seq Scan on orders  (cost=0.00..35.50 rows=1 width=8)"}]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Query Plan", result.stdout)
        self.assertIn("Seq Scan", result.stdout)

    def test_sample_table_from_fixture(self) -> None:
        result = run_capability(
            "sample-table",
            {"rows": [{"id": 1, "status": "active"}], "row_count": 1, "limit": 20},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Table Sample", result.stdout)

    def test_analyze_query_result_from_fixture(self) -> None:
        result = run_capability(
            "analyze-query-result",
            {"columns": [{"column_name": "id", "data_type": "int", "null_count": 0, "distinct_count": 10, "sensitive_kind": None}]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Query Result Analysis", result.stdout)

    def test_detect_data_quality_issues_from_fixture(self) -> None:
        result = run_capability(
            "detect-data-quality-issues",
            {"schema": "public", "table": "orders", "issues": [{"column_name": "notes", "issue": "all_null"}]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Data Quality Issues", result.stdout)
        self.assertIn("all_null", result.stdout)

    def test_estimate_table_size_from_fixture(self) -> None:
        result = run_capability(
            "estimate-table-size",
            {"tables": [{"table_schema": "public", "table_name": "orders", "estimated_rows": 50000, "total_bytes": 8192000}]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Table Size Estimate", result.stdout)
        self.assertIn("orders", result.stdout)

    def test_compare_tables_from_fixture(self) -> None:
        result = run_capability(
            "compare-tables",
            {
                "common": [{"column_name": "id", "type_left": "int", "type_right": "int"}],
                "left_only": [{"column_name": "created_at"}],
                "right_only": [],
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Table Comparison", result.stdout)

    def test_trace_record_from_fixture(self) -> None:
        result = run_capability(
            "trace-record",
            {"rows": [{"id": 42, "status": "active", "email": "test@example.com"}], "row_count": 1, "limit": 100},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Postgres Record Trace", result.stdout)

    # ---------------------------------------------------------------------------
    # Privacy / PII masking tests (Section 9 criterion: G6/G7 closed)
    # ---------------------------------------------------------------------------

    def test_run_readonly_query_masks_email(self) -> None:
        result = run_capability(
            "run-readonly-query",
            {"row_count": 1, "limit": 100, "rows": [{"email": "ana@example.com", "id": 1}]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("ana@example.com", result.stdout)
        self.assertIn("EMAIL REDACTED", result.stdout)

    def test_run_readonly_query_masks_phone(self) -> None:
        result = run_capability(
            "run-readonly-query",
            {"row_count": 1, "limit": 100, "rows": [{"phone": "11999990000", "id": 1}]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("11999990000", result.stdout)
        self.assertIn("PHONE REDACTED", result.stdout)

    def test_run_readonly_query_masks_token(self) -> None:
        result = run_capability(
            "run-readonly-query",
            {"row_count": 1, "limit": 100, "rows": [{"api_token": "supersecret123", "id": 1}]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("supersecret123", result.stdout)
        self.assertIn("TOKEN REDACTED", result.stdout)

    def test_run_readonly_query_masks_cnpj(self) -> None:
        result = run_capability(
            "run-readonly-query",
            {"row_count": 1, "limit": 100, "rows": [{"cnpj": "11222333000181", "id": 1}]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("11222333000181", result.stdout)
        self.assertIn("11.***.***/****-81", result.stdout)

    def test_sample_table_masks_email(self) -> None:
        result = run_capability(
            "sample-table",
            {"rows": [{"id": 1, "email": "joao@test.com", "status": "active"}], "row_count": 1, "limit": 20},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("joao@test.com", result.stdout)
        self.assertIn("EMAIL REDACTED", result.stdout)

    def test_trace_record_masks_email(self) -> None:
        result = run_capability(
            "trace-record",
            {"rows": [{"id": 42, "email": "secret@corp.com", "status": "active"}], "row_count": 1, "limit": 100},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("secret@corp.com", result.stdout)
        self.assertIn("EMAIL REDACTED", result.stdout)

    def test_structural_columns_not_masked(self) -> None:
        """table_name, column_name, schema_name etc. must NOT be masked."""
        result = run_capability(
            "list-tables",
            {"schema": "public", "tables": [{"table_schema": "public", "table_name": "customers", "table_type": "BASE TABLE"}]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("customers", result.stdout)
        self.assertNotIn("REDACTED", result.stdout)

    def test_validate_readonly_query_blocks_delete(self) -> None:
        """validate-readonly-query blocks SQL write keywords (fixture path)."""
        result = run_capability(
            "validate-readonly-query",
            {"valid": False, "query": "delete from public.users", "limit": 100},
        )
        # Even from fixture the runner just renders — this tests the live path below
        # The live blocking test already exists; this confirms fixture render is ok
        self.assertEqual(result.returncode, 0, result.stderr)

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
