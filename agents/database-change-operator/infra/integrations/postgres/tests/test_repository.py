#!/usr/bin/env python3
"""Unit tests for database change repository helpers."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


POSTGRES_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(POSTGRES_DIR))

from database_change_repository import (  # pylint: disable=import-error
    DatabaseChangeRepositoryError,
    build_upsert_sql,
    connection_database,
    connection_env,
    migration_id_from_path,
    plan_sql,
    rollback_path_for,
    validate_database_name,
    validate_where_clause,
    with_database_override,
)


class DatabaseChangeRepositoryHelperTest(unittest.TestCase):
    def test_plan_blocks_dangerous_sql(self) -> None:
        plan = plan_sql("drop database prod;")

        self.assertTrue(plan["blocked"])
        self.assertEqual(plan["statement_count"], 1)

    def test_plan_marks_destructive_sql(self) -> None:
        plan = plan_sql("drop table public.old_table;")

        self.assertTrue(plan["destructive"])

    def test_plan_detects_non_transactional_sql(self) -> None:
        plan = plan_sql("create index concurrently idx_customer_name on customers(name);")

        self.assertFalse(plan["transactional"])

    def test_connection_env_parses_url_without_process_argument_secret(self) -> None:
        env = connection_env("postgres://user:pass%20word@localhost:5432/app?sslmode=require")

        self.assertEqual(env["PGHOST"], "localhost")
        self.assertEqual(env["PGPORT"], "5432")
        self.assertEqual(env["PGUSER"], "user")
        self.assertEqual(env["PGPASSWORD"], "pass word")
        self.assertEqual(env["PGDATABASE"], "app")
        self.assertEqual(env["PGSSLMODE"], "require")

    def test_with_database_override_changes_only_database_name(self) -> None:
        connection = with_database_override("postgres://user:pass@localhost:5432/app?sslmode=require", "audit_db")

        self.assertEqual(connection, "postgres://user:pass@localhost:5432/audit_db?sslmode=require")
        self.assertEqual(connection_database(connection), "audit_db")

    def test_validate_database_name_rejects_url_or_path(self) -> None:
        for value in ("postgres://host/db", "audit/db", "audit db", "audit#db"):
            with self.subTest(value=value):
                with self.assertRaises(Exception):
                    validate_database_name(value)

    def test_migration_id_uses_filename_without_direction_suffix(self) -> None:
        self.assertEqual(migration_id_from_path("/tmp/202606211200_create_table.up.sql"), "202606211200_create_table")
        self.assertEqual(migration_id_from_path("/tmp/202606211200_create_table.down.sql"), "202606211200_create_table")

    def test_rollback_path_for_finds_sibling_down_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            up = Path(tmpdir) / "001_create_table.up.sql"
            down = Path(tmpdir) / "001_create_table.down.sql"
            up.write_text("create table x(id int);", encoding="utf-8")
            down.write_text("drop table x;", encoding="utf-8")

            self.assertEqual(rollback_path_for(str(up)), str(down))

    def test_build_upsert_sql_uses_conflict_update(self) -> None:
        sql = build_upsert_sql(
            "public",
            "customers",
            "id",
            [{"id": "1", "name": "Ana"}],
            ["id", "name"],
        )

        self.assertIn('on conflict ("id") do update set "name" = excluded."name"', sql)

    def test_build_upsert_sql_uses_do_nothing_when_only_key_column(self) -> None:
        sql = build_upsert_sql("public", "customers", "id", [{"id": "1"}], ["id"])

        self.assertIn('on conflict ("id") do nothing', sql)

    def test_validate_where_clause_rejects_broad_or_multi_statement_where(self) -> None:
        with self.assertRaises(Exception):
            validate_where_clause("1=1")
        with self.assertRaises(Exception):
            validate_where_clause("id = 1; delete from customers")

    def test_plan_sql_destructive_delete_is_flagged(self) -> None:
        """G7: DELETE FROM must be classified as destructive."""
        plan = plan_sql("delete from public.old_events where created_at < '2020-01-01';")
        self.assertTrue(plan["destructive"])
        self.assertFalse(plan["blocked"])

    def test_plan_sql_blocked_grant_is_flagged(self) -> None:
        """Guardrail: GRANT must be blocked."""
        plan = plan_sql("grant select on public.customers to readonly_user;")
        self.assertTrue(plan["blocked"])


if __name__ == "__main__":
    unittest.main()
