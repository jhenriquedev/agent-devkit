#!/usr/bin/env python3
"""Tests for TOPdesk repository helpers."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


TOPDESK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOPDESK_DIR))

from topdesk_repository import TopdeskConfig, TopdeskRepository  # noqa: E402


class TopdeskRepositoryTest(unittest.TestCase):
    def test_config_reads_app_password_from_env(self) -> None:
        env = {
            "TOPDESK_BASE_URL": "https://example.topdesk.net",
            "TOPDESK_USERNAME": "agent",
            "TOPDESK_APP_PASSWORD": "secret",
        }
        with patch("topdesk_repository.load_dotenv", lambda: None), patch.dict(
            os.environ, env, clear=True
        ):
            config = TopdeskConfig.from_env()

        self.assertEqual(config.base_url, "https://example.topdesk.net")
        self.assertEqual(config.username, "agent")
        self.assertEqual(config.app_password, "secret")

    def test_config_accepts_password_fallback(self) -> None:
        env = {
            "TOPDESK_BASE_URL": "https://example.topdesk.net/",
            "TOPDESK_USERNAME": "agent",
            "TOPDESK_PASSWORD": "legacy-secret",
        }
        with patch("topdesk_repository.load_dotenv", lambda: None), patch.dict(
            os.environ, env, clear=True
        ):
            config = TopdeskConfig.from_env()

        self.assertEqual(config.base_url, "https://example.topdesk.net")
        self.assertEqual(config.app_password, "legacy-secret")

    def test_builds_api_url_with_query(self) -> None:
        repo = TopdeskRepository(
            TopdeskConfig(
                base_url="https://example.topdesk.net",
                username="agent",
                app_password="secret",
            )
        )

        self.assertEqual(
            repo._url("/incidents", {"query": "email login", "page_size": "10"}),
            "https://example.topdesk.net/tas/api/incidents?query=email+login&page_size=10",
        )

    def test_normalizes_incident_lookup_fields(self) -> None:
        normalized = TopdeskRepository._normalize_incident(
            {
                "id": "abc-123",
                "number": "I 2606 001",
                "briefDescription": "Erro no acesso",
                "request": "Usuario informa falha ao acessar o portal.",
                "status": {"name": "In progress"},
                "category": {"name": "Software"},
                "priority": {"name": "P2"},
                "operatorGroup": {"name": "Service Desk"},
                "caller": {"name": "Ana Silva"},
                "creationDate": "2026-06-21T10:00:00Z",
            }
        )

        self.assertEqual(normalized["id"], "abc-123")
        self.assertEqual(normalized["number"], "I 2606 001")
        self.assertEqual(normalized["status"], "In progress")
        self.assertEqual(normalized["category"], "Software")
        self.assertEqual(normalized["priority"], "P2")
        self.assertEqual(normalized["operator_group"], "Service Desk")
        self.assertEqual(normalized["caller"], "Ana Silva")
        self.assertEqual(normalized["creation_date"], "2026-06-21T10:00:00Z")

    def test_request_does_not_pass_password_in_curl_argv_and_sets_timeout(self) -> None:
        secret = "local-topdesk-password"
        repo = TopdeskRepository(
            TopdeskConfig(
                base_url="https://example.topdesk.net",
                username="agent",
                app_password=secret,
            )
        )
        captured_command: list[str] = []
        captured_timeout: list[int | None] = []
        captured_curl_config: list[str] = []

        def fake_run(command: list[str], **kwargs: object) -> object:
            captured_command[:] = command
            captured_timeout[:] = [kwargs.get("timeout")]  # type: ignore[list-item]
            if "--config" in command:
                captured_curl_config[:] = [Path(command[command.index("--config") + 1]).read_text(encoding="utf-8")]
            response_path = Path(command[command.index("-o") + 1])
            response_path.write_text("[]", encoding="utf-8")
            return type("Completed", (), {"returncode": 0, "stdout": "200", "stderr": ""})()

        with patch("subprocess.run", side_effect=fake_run):
            repo.list_incidents(limit=1)

        self.assertNotIn(secret, captured_command)
        self.assertNotIn(f"agent:{secret}", captured_command)
        self.assertIn("--config", captured_command)
        self.assertIn("--max-time", captured_command)
        self.assertEqual(captured_command[captured_command.index("--max-time") + 1], "30")
        self.assertEqual(captured_timeout[0], 35)
        self.assertTrue(captured_curl_config)
        self.assertIn(f'user = "agent:{secret}"', captured_curl_config[0])


if __name__ == "__main__":
    unittest.main()
