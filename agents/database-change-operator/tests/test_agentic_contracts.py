#!/usr/bin/env python3
"""Agentic contract tests for the Database Change Operator package."""

from __future__ import annotations

import unittest
from pathlib import Path


AGENT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (AGENT / relative_path).read_text(encoding="utf-8")


class DatabaseChangeOperatorAgenticContractsTest(unittest.TestCase):
    def test_write_capabilities_document_execution_boundaries(self) -> None:
        expected_markers = {
            "test-write-permissions": ["--execute", "rollback", "statement_timeout", "lock_timeout"],
            "apply-migration": ["--execute", "ai_devkit_migrations", "statement_timeout", "lock_timeout"],
            "rollback-migration": ["--execute", ".down.sql", "ai_devkit_migrations", "statement_timeout"],
            "run-write-script": ["--execute", "dry-run", "ai_devkit_write_audit", "confirmacao destrutiva"],
            "upsert-records": ["--execute", "dry-run", "ai_devkit_write_audit", "max_affected_rows"],
            "update-records": ["--execute", "preview", "ai_devkit_write_audit", "max_affected_rows"],
        }

        for capability_id, markers in expected_markers.items():
            with self.subTest(capability=capability_id):
                capability = read(f"capabilities/{capability_id}/capability.yaml")
                rules = read(f"capabilities/{capability_id}/decision-rules.md").lower()

                self.assertIn("write_policy: confirm", capability)
                for marker in markers:
                    self.assertIn(marker, rules)

    def test_database_override_contract_is_documented(self) -> None:
        policies = read("knowledge/policies.yaml").lower()
        system_prompt = read("knowledge/system.md").lower()

        for marker in ("override_scope", "database_name_only", "reject_url_as_database_name"):
            self.assertIn(marker, policies)
        self.assertIn("target database", system_prompt)
        self.assertIn("connection string", system_prompt)


if __name__ == "__main__":
    unittest.main()
