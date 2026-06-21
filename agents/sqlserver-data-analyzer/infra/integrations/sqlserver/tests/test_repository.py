#!/usr/bin/env python3
"""Tests for SQL Server repository helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


SQLSERVER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SQLSERVER_DIR))

from sqlserver_repository import (  # noqa: E402
    SqlServerRepositoryError,
    enforce_top,
    sensitive_kind,
    validate_database_name,
    validate_identifier,
    validate_readonly_query,
)


class SqlServerRepositoryHelperTest(unittest.TestCase):
    def test_validate_readonly_query_allows_select(self) -> None:
        self.assertEqual(validate_readonly_query("select 1;"), "select 1")

    def test_validate_readonly_query_blocks_write(self) -> None:
        with self.assertRaises(SqlServerRepositoryError):
            validate_readonly_query("merge dbo.users as target using dbo.stage as source on 1=1")

    def test_enforce_top_adds_top_to_select(self) -> None:
        limited = enforce_top("select * from dbo.users", 50)

        self.assertEqual(limited, "select top (50) * from dbo.users")

    def test_validate_identifier_allows_schema_table(self) -> None:
        validate_identifier("dbo", "schema")
        validate_identifier("CustomerOrders", "table")

    def test_validate_database_name_rejects_path_like_value(self) -> None:
        with self.assertRaises(SqlServerRepositoryError):
            validate_database_name("master;drop database app")

    def test_sensitive_kind_detects_token(self) -> None:
        self.assertEqual(sensitive_kind("access_token"), "token")


if __name__ == "__main__":
    unittest.main()
