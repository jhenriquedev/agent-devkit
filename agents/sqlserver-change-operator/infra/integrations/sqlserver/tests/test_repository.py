#!/usr/bin/env python3
"""Tests for SQL Server change repository helpers."""

from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
