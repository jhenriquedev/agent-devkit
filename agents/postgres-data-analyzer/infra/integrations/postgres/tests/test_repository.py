#!/usr/bin/env python3
"""Tests for Postgres repository helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


POSTGRES_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(POSTGRES_DIR))

from postgres_repository import (  # noqa: E402
    PostgresRepositoryError,
    connection_database,
    connection_env,
    enforce_limit,
    validate_readonly_query,
    validate_database_name,
    sensitive_kind,
    with_database_override,
)


class PostgresRepositoryHelperTest(unittest.TestCase):
    def test_connection_env_parses_url(self) -> None:
        env = connection_env("postgresql://user:pass@localhost:5432/app?sslmode=require")

        self.assertEqual(env["PGHOST"], "localhost")
        self.assertEqual(env["PGPORT"], "5432")
        self.assertEqual(env["PGUSER"], "user")
        self.assertEqual(env["PGPASSWORD"], "pass")
        self.assertEqual(env["PGDATABASE"], "app")
        self.assertEqual(env["PGSSLMODE"], "require")

    def test_with_database_override_changes_only_database_name(self) -> None:
        connection = with_database_override("postgresql://user:pass@localhost:5432/app?sslmode=require", "other_db")

        self.assertEqual(connection, "postgresql://user:pass@localhost:5432/other_db?sslmode=require")
        self.assertEqual(connection_database(connection), "other_db")

    def test_validate_database_name_rejects_url_or_path(self) -> None:
        for value in ("postgres://host/db", "other/db", "other db", "other?sslmode=disable"):
            with self.subTest(value=value):
                with self.assertRaises(PostgresRepositoryError):
                    validate_database_name(value)

    def test_validate_readonly_query_allows_select(self) -> None:
        self.assertEqual(validate_readonly_query("select 1;"), "select 1")

    def test_validate_readonly_query_blocks_write(self) -> None:
        with self.assertRaises(PostgresRepositoryError):
            validate_readonly_query("delete from public.users")

    def test_enforce_limit_wraps_query(self) -> None:
        limited = enforce_limit("select * from public.users", 50)

        self.assertIn("limit 50", limited)

    def test_sensitive_kind_detects_cpf(self) -> None:
        self.assertEqual(sensitive_kind("customer_cpf"), "cpf")


if __name__ == "__main__":
    unittest.main()
