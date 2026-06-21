#!/usr/bin/env python3
"""Smoke tests for Database Change Operator runners through ai-devkit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


PLAN = {
    "path": "001_create_table.up.sql",
    "checksum": "abc123",
    "statement_count": 1,
    "operations": [{"command": "create table", "preview": "create table public.customers(id int)"}],
    "blocked": False,
    "destructive": False,
    "transactional": True,
    "rollback_path": "001_create_table.down.sql",
    "requires_execute": True,
}


class DatabaseChangeRunnerSmokeTest(unittest.TestCase):
    def test_write_permission_from_fixture(self) -> None:
        result = run_capability(
            "test-write-permissions",
            {"dry_run": False, "write_permissions": True, "rolled_back": True},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Database Write Permissions", result.stdout)
        self.assertIn("Write permissions: yes", result.stdout)

    def test_plan_migration_from_fixture(self) -> None:
        result = run_capability("plan-migration", PLAN, ["--path", "001_create_table.up.sql"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Migration Plan", result.stdout)
        self.assertIn("create table", result.stdout)

    def test_apply_migration_from_fixture(self) -> None:
        result = run_capability(
            "apply-migration",
            {"dry_run": True, "migration_id": "001_create_table", "plan": PLAN},
            ["--path", "001_create_table.up.sql"],
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Apply Migration", result.stdout)
        self.assertIn("Re-run with `--execute`", result.stdout)

    def test_rollback_migration_from_fixture(self) -> None:
        result = run_capability(
            "rollback-migration",
            {"dry_run": True, "migration_id": "001_create_table", "plan": PLAN},
            ["--path", "001_create_table.down.sql"],
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Rollback Migration", result.stdout)
        self.assertIn("001_create_table", result.stdout)

    def test_run_write_script_from_fixture(self) -> None:
        result = run_capability(
            "run-write-script",
            {"dry_run": True, "plan": PLAN},
            ["--path", "fix_customer.sql"],
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Run Write Script", result.stdout)

    def test_upsert_records_from_fixture(self) -> None:
        result = run_capability(
            "upsert-records",
            {"dry_run": True, "record_count": 2, "plan": PLAN},
            ["--schema", "public", "--table", "customers", "--key-column", "id", "--input", "records.json"],
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Upsert Records", result.stdout)
        self.assertIn("Record count: 2", result.stdout)

    def test_update_records_from_fixture(self) -> None:
        result = run_capability(
            "update-records",
            {"dry_run": True, "where_sql": "id = 1", "plan": PLAN},
            ["--schema", "public", "--table", "customers", "--set-json", '{"name":"Ana"}', "--where", "id = 1"],
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Update Records", result.stdout)
        self.assertIn("Where: id = 1", result.stdout)

    def test_migration_report_from_fixture(self) -> None:
        result = run_capability(
            "migration-report",
            {
                "count": 1,
                "migrations": [
                    {
                        "id": "001_create_table",
                        "name": "001_create_table.up.sql",
                        "status": "applied",
                        "applied_at": "2026-06-21T12:00:00Z",
                        "rollback_available": True,
                    }
                ],
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Migration Report", result.stdout)
        self.assertIn("001_create_table", result.stdout)

    def test_database_override_is_rendered_from_fixture(self) -> None:
        result = run_capability(
            "migration-report",
            {"count": 0, "migrations": []},
            ["--database", "other_db"],
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("- Target database: other_db", result.stdout)


def run_capability(capability: str, fixture: dict, extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_path = Path(tmpdir) / "fixture.json"
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(CLI),
                "run",
                "database-change-operator",
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
