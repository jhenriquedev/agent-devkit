#!/usr/bin/env python3
"""Tests for AzureRepository project handling."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


AZURE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AZURE_DIR))

from azure_repository import AzureConfig, AzureRepository  # noqa: E402


class AzureRepositoryProjectTest(unittest.TestCase):
    def test_config_allows_no_default_project(self) -> None:
        config = AzureConfig(org="example-org", pat="token")

        self.assertEqual(config.org, "example-org")
        self.assertIsNone(config.default_project)

    def test_repository_builds_project_url_per_call(self) -> None:
        config = AzureConfig(
            org="example-org",
            pat="token",
            default_project=None,
            api_version="7.1",
        )
        repo = AzureRepository(config)

        self.assertIn("/Project A/", repo._url("Project A", "_apis/wit/workitems/123"))

    def test_normalizes_card_metadata(self) -> None:
        normalized = AzureRepository._normalize_work_item(
            {
                "id": 123,
                "rev": 4,
                "fields": {
                    "System.WorkItemType": "Issue",
                    "System.Title": "Card com alerta",
                    "System.State": "To Do",
                    "System.CreatedDate": "2026-06-19T19:21:04.407Z",
                    "System.ChangedDate": "2026-06-20T16:51:04.757Z",
                    "System.BoardColumn": "Backlog",
                    "System.BoardColumnDone": False,
                    "System.Tags": "prd; Warning",
                },
            }
        )

        self.assertEqual(normalized["created_date"], "2026-06-19T19:21:04.407Z")
        self.assertEqual(normalized["changed_date"], "2026-06-20T16:51:04.757Z")
        self.assertEqual(normalized["board_column"], "Backlog")
        self.assertFalse(normalized["board_column_done"])


if __name__ == "__main__":
    unittest.main()
