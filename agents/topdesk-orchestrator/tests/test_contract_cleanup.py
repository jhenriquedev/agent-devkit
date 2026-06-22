#!/usr/bin/env python3
"""Contract cleanup tests for TOPdesk Orchestrator."""

from __future__ import annotations

import unittest
from pathlib import Path


AGENT = Path(__file__).resolve().parents[1]


class TopdeskContractCleanupTest(unittest.TestCase):
    def test_env_example_does_not_document_removed_raw_mutation_flag(self) -> None:
        env_example = AGENT / "infra" / "integrations" / "topdesk" / "env.example"

        self.assertNotIn("TOPDESK_ALLOW_RAW_MUTATIONS", env_example.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
