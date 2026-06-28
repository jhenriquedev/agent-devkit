#!/usr/bin/env python3
"""Smoke tests for SQL Server Change Operator through ai-devkit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "ai-devkit"
AGENT = "sqlserver-change-operator"


PLAN = {
    "path": "001_create_table.up.sql",
    "checksum": "abc123",
    "statement_count": 1,
    "operations": [{"command": "create table", "preview": "create table dbo.Customers(id int)"}],
    "blocked": False,
    "destructive": False,
    "transactional": True,
    "rollback_path": "001_create_table.down.sql",
    "requires_execute": True,
    "risk_level": "medium",
}


class SqlServerChangeOperatorSmokeTest(unittest.TestCase):
    def test_plan_migration_from_fixture(self) -> None:
        result = run_capability("plan-migration", PLAN, ["--path", "001_create_table.up.sql"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# SQL Server Migration Plan", result.stdout)
        self.assertIn("create table", result.stdout)

    def test_apply_migration_dry_run_from_fixture(self) -> None:
        result = run_capability(
            "apply-migration",
            {"dry_run": True, "migration_id": "001_create_table", "plan": PLAN},
            ["--path", "001_create_table.up.sql"],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# SQL Server Apply Migration", result.stdout)
        self.assertIn("Re-run with `--execute`", result.stdout)

    def test_delete_records_requires_confirmation(self) -> None:
        result = run_cli(
            "run",
            AGENT,
            "delete-records",
            "--schema",
            "dbo",
            "--table",
            "Customers",
            "--where",
            "id = 1",
            "--execute",
            "--confirm-execute",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--confirm-delete is required", result.stderr)

    def test_update_records_from_fixture(self) -> None:
        result = run_capability(
            "update-records",
            {"dry_run": True, "where_sql": "id = 1", "max_affected_rows": 100, "plan": PLAN},
            ["--schema", "dbo", "--table", "Customers", "--set-json", '{"name":"Ana"}', "--where", "id = 1"],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# SQL Server Update Records", result.stdout)
        self.assertIn("Where: id = 1", result.stdout)


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
