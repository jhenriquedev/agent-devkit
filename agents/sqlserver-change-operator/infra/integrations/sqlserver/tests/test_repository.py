#!/usr/bin/env python3
"""Tests for SQL Server change repository helpers."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SQLSERVER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SQLSERVER_DIR))

from sqlserver_change_repository import (  # noqa: E402
    SqlServerChangeRepositoryError,
    plan_sql,
    validate_where_clause,
)


class SqlServerChangeRepositoryHelperTest(unittest.TestCase):
    def test_plan_sql_blocks_drop_database(self) -> None:
        plan = plan_sql("drop database Production;")

        self.assertTrue(plan["blocked"])
        self.assertEqual(plan["risk_level"], "blocked")

    def test_plan_sql_marks_delete_destructive(self) -> None:
        plan = plan_sql("delete from dbo.Customers where id = 1;")

        self.assertTrue(plan["destructive"])
        self.assertEqual(plan["risk_level"], "high")

    def test_validate_where_clause_rejects_empty_or_broad_clause(self) -> None:
        for value in ("", "1=1", "true"):
            with self.subTest(value=value):
                with self.assertRaises(SqlServerChangeRepositoryError):
                    validate_where_clause(value)

    def test_plan_migration_detects_rollback_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            up = Path(tmpdir) / "001_create_table.up.sql"
            down = Path(tmpdir) / "001_create_table.down.sql"
            up.write_text("create table dbo.Customers(id int);", encoding="utf-8")
            down.write_text("drop table dbo.Customers;", encoding="utf-8")

            plan = plan_sql(up.read_text(encoding="utf-8"), path=str(up))

        self.assertEqual(plan["rollback_path"], str(down))


class SqlServerChangeRepositoryGuardrailTest(unittest.TestCase):
    def test_enforce_affected_limit_raises_when_exceeded(self) -> None:
        from sqlserver_change_repository import enforce_affected_limit, SqlServerChangeRepositoryError
        with self.assertRaises(SqlServerChangeRepositoryError):
            enforce_affected_limit(101, 100)

    def test_enforce_affected_limit_passes_at_limit(self) -> None:
        from sqlserver_change_repository import enforce_affected_limit
        # Should not raise
        enforce_affected_limit(100, 100)

    def test_build_upsert_sql_raises_when_key_column_missing(self) -> None:
        from sqlserver_change_repository import build_upsert_sql, SqlServerChangeRepositoryError
        records = [{"name": "Alice", "age": "30"}]
        with self.assertRaises(SqlServerChangeRepositoryError):
            build_upsert_sql("dbo", "users", "id", records)

    def test_build_upsert_sql_generates_if_exists_pattern(self) -> None:
        from sqlserver_change_repository import build_upsert_sql
        records = [{"id": "1", "name": "Alice"}]
        sql = build_upsert_sql("dbo", "users", "id", records)
        self.assertIn("if exists", sql.lower())
        self.assertIn("update", sql.lower())
        self.assertIn("insert", sql.lower())

    def test_wrap_in_transaction_wraps_transactional_sql(self) -> None:
        from sqlserver_change_repository import wrap_in_transaction, SqlServerChangeConfig
        config = SqlServerChangeConfig(connection_string="Server=localhost;")
        result = wrap_in_transaction("insert into dbo.t(id) values(1);", config)
        self.assertIn("begin transaction", result.lower())
        self.assertIn("commit transaction", result.lower())

    def test_wrap_in_transaction_skips_transaction_for_non_transactional(self) -> None:
        from sqlserver_change_repository import wrap_in_transaction, SqlServerChangeConfig
        config = SqlServerChangeConfig(connection_string="Server=localhost;")
        # backup is NON_TRANSACTIONAL
        result = wrap_in_transaction("backup log mydb to disk='x';", config)
        self.assertNotIn("begin transaction", result.lower())

    def test_validate_identifier_rejects_invalid(self) -> None:
        from sqlserver_change_repository import validate_identifier, SqlServerChangeRepositoryError
        for bad in ("1bad", "has space", "drop;", ""):
            with self.subTest(value=bad):
                with self.assertRaises(SqlServerChangeRepositoryError):
                    validate_identifier(bad, "col")

    def test_validate_identifier_accepts_valid(self) -> None:
        from sqlserver_change_repository import validate_identifier
        for good in ("MyTable", "_private", "col123", "schema$name"):
            with self.subTest(value=good):
                validate_identifier(good, "col")  # should not raise

    def test_with_database_override_replaces_database(self) -> None:
        from sqlserver_change_repository import with_database_override
        conn = "Server=localhost;Database=OldDb;Trusted_Connection=yes"
        result = with_database_override(conn, "NewDb")
        self.assertIn("Database=NewDb", result)
        self.assertNotIn("OldDb", result)

    def test_with_database_override_no_op_when_none(self) -> None:
        from sqlserver_change_repository import with_database_override
        conn = "Server=localhost;Database=OldDb;"
        result = with_database_override(conn, None)
        self.assertEqual(result, conn)


_SHARED_DIR = Path(__file__).resolve().parents[4] / "capabilities" / "_shared"


def load_runner_support():
    spec = importlib.util.spec_from_file_location(
        "sqlserver_change_operator_runner_support",
        _SHARED_DIR / "runner_support.py",
    )
    if spec is None or spec.loader is None:
        raise ImportError("cannot load sqlserver change runner_support")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SqlServerRunnerPreflight(unittest.TestCase):
    def test_preflight_blocks_delete_execute_without_confirm_delete(self) -> None:
        import argparse
        from sqlserver_change_repository import SqlServerChangeRepositoryError
        preflight = load_runner_support().preflight
        args = argparse.Namespace(execute=True, confirm_delete=False)
        with self.assertRaises(SqlServerChangeRepositoryError):
            preflight("delete-records", args)

    def test_preflight_allows_delete_execute_with_confirm_delete(self) -> None:
        import argparse
        preflight = load_runner_support().preflight
        args = argparse.Namespace(execute=True, confirm_delete=True)
        preflight("delete-records", args)  # should not raise


if __name__ == "__main__":
    unittest.main()
