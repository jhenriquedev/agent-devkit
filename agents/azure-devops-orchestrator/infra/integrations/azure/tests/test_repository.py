#!/usr/bin/env python3
"""Tests for AzureRepository project handling."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


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

    def test_request_does_not_pass_pat_in_curl_argv_and_sets_timeout(self) -> None:
        secret = "local-azure-pat"
        repo = AzureRepository(AzureConfig(org="example-org", pat=secret, api_version="7.1"))
        captured_command: list[str] = []
        captured_timeout: list[int | None] = []
        captured_curl_config: list[str] = []

        def fake_run(command: list[str], **kwargs: object) -> object:
            captured_command[:] = command
            captured_timeout[:] = [kwargs.get("timeout")]  # type: ignore[list-item]
            if "--config" in command:
                captured_curl_config[:] = [Path(command[command.index("--config") + 1]).read_text(encoding="utf-8")]
            response_path = Path(command[command.index("-o") + 1])
            response_path.write_text("{}", encoding="utf-8")
            return type("Completed", (), {"returncode": 0, "stdout": "200", "stderr": ""})()

        with patch("subprocess.run", side_effect=fake_run):
            repo.get_work_item(123, project="Project A")

        self.assertNotIn(secret, captured_command)
        self.assertNotIn(f":{secret}", captured_command)
        self.assertIn("--config", captured_command)
        self.assertIn("--max-time", captured_command)
        self.assertEqual(captured_command[captured_command.index("--max-time") + 1], "30")
        self.assertEqual(captured_timeout[0], 35)
        self.assertTrue(captured_curl_config)
        self.assertIn(f'user = ":{secret}"', captured_curl_config[0])

    def test_attachment_upload_does_not_pass_pat_in_curl_argv_and_sets_timeout(self) -> None:
        secret = "local-azure-pat"
        repo = AzureRepository(AzureConfig(org="example-org", pat=secret, api_version="7.1"))
        captured_command: list[str] = []
        captured_timeout: list[int | None] = []
        captured_curl_config: list[str] = []

        def fake_run(command: list[str], **kwargs: object) -> object:
            captured_command[:] = command
            captured_timeout[:] = [kwargs.get("timeout")]  # type: ignore[list-item]
            if "--config" in command:
                captured_curl_config[:] = [Path(command[command.index("--config") + 1]).read_text(encoding="utf-8")]
            return type(
                "Completed",
                (),
                {"returncode": 0, "stdout": '{"url":"https://dev.azure.com/uploaded"}', "stderr": ""},
            )()

        with patch("subprocess.run", side_effect=fake_run):
            result = repo._upload_attachment("Project A", "/tmp/evidence.txt", "evidence.txt")

        self.assertEqual(result["url"], "https://dev.azure.com/uploaded")
        self.assertNotIn(secret, captured_command)
        self.assertNotIn(f":{secret}", captured_command)
        self.assertIn("--config", captured_command)
        self.assertIn("--max-time", captured_command)
        self.assertEqual(captured_command[captured_command.index("--max-time") + 1], "30")
        self.assertEqual(captured_timeout[0], 35)
        self.assertTrue(captured_curl_config)
        self.assertIn(f'user = ":{secret}"', captured_curl_config[0])


if __name__ == "__main__":
    unittest.main()
