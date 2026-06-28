#!/usr/bin/env python3
"""Wave 3 contracts for persistent conversation sessions."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "agent"
CLI_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_CLI_TIMEOUT_SECONDS", "60"))


class AgenticWave3ContractsTest(unittest.TestCase):
    def run_agent(
        self,
        *args: str,
        env: dict[str, str],
        cwd: Path = ROOT,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(AGENT), *args],
            cwd=cwd,
            env=os.environ | env,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CLI_TIMEOUT_SECONDS,
        )

    def test_sessions_shortcut_lists_empty_session_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_agent("--json", "-s", env={"AI_DEVKIT_CONFIG_HOME": tmpdir})

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["kind"], "sessions")
            self.assertEqual(payload["items"], [])
            self.assertEqual(payload["home"], str((Path(tmpdir) / "sessions").resolve()))

    def test_agent_prompt_creates_default_session_and_local_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            result = self.run_agent("--json", "qual", "seu", "nome?", env=env)

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            session = payload["session"]
            session_path = Path(session["path"])
            self.assertTrue(session["active"])
            self.assertEqual(session["exchange_count"], 1)
            self.assertGreater(session["token_estimate"], 0)
            self.assertTrue((session_path / "state.json").is_file())
            self.assertTrue((session_path / "summary.md").is_file())
            self.assertTrue((session_path / "messages.jsonl").is_file())
            self.assertEqual(len((session_path / "messages.jsonl").read_text(encoding="utf-8").splitlines()), 1)

    def test_new_session_and_explicit_resume_append_to_same_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            first = self.run_agent("--json", "--new-session", "qual", "seu", "nome?", env=env)
            first_payload = json.loads(first.stdout)
            session_id = first_payload["session"]["id"]
            first_tokens = first_payload["session"]["token_estimate"]

            second = self.run_agent("--json", "--session", session_id, "qual", "seu", "nome?", env=env)
            second_payload = json.loads(second.stdout)
            show = self.run_agent("session", "show", session_id, "--json", env=env)

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(show.returncode, 0, show.stderr)
            self.assertEqual(second_payload["session"]["id"], session_id)
            self.assertEqual(second_payload["session"]["exchange_count"], 2)
            self.assertGreater(second_payload["session"]["token_estimate"], first_tokens)
            show_payload = json.loads(show.stdout)
            self.assertEqual(show_payload["session"]["id"], session_id)
            self.assertEqual(len(show_payload["recent_messages"]), 2)

    def test_session_resume_marks_active_for_next_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            first = self.run_agent("--json", "--new-session", "qual", "seu", "nome?", env=env)
            session_id = json.loads(first.stdout)["session"]["id"]
            resumed = self.run_agent("session", "resume", session_id, "--json", env=env)
            next_prompt = self.run_agent("--json", "qual", "seu", "nome?", env=env)

            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertEqual(next_prompt.returncode, 0, next_prompt.stderr)
            self.assertEqual(json.loads(resumed.stdout)["status"], "resumed")
            self.assertEqual(json.loads(next_prompt.stdout)["session"]["id"], session_id)
            self.assertEqual(json.loads(next_prompt.stdout)["session"]["exchange_count"], 2)

    def test_memory_reset_sessions_tasks_and_cache_is_granular(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            create = self.run_agent("--json", "qual", "seu", "nome?", env=env)
            (home / "tasks" / "job.md").write_text("job", encoding="utf-8")
            (home / "cache" / "item.txt").write_text("cache", encoding="utf-8")

            reset = self.run_agent("memory", "reset", "--sessions", "--tasks", "--cache", "--json", env=env)
            listing = self.run_agent("session", "list", "--json", env=env)

            self.assertEqual(create.returncode, 0, create.stderr)
            self.assertEqual(reset.returncode, 0, reset.stderr)
            payload = json.loads(reset.stdout)
            self.assertTrue(payload["sessions_reset"])
            self.assertTrue(payload["tasks_reset"])
            self.assertTrue(payload["cache_reset"])
            self.assertEqual(json.loads(listing.stdout)["items"], [])
            self.assertFalse((home / "tasks" / "job.md").exists())
            self.assertFalse((home / "cache" / "item.txt").exists())

    def test_active_session_does_not_bleed_between_projects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as project_dir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            first = self.run_agent("--json", "qual", "seu", "nome?", env=env, cwd=ROOT)
            second = self.run_agent("--json", "qual", "seu", "nome?", env=env, cwd=Path(project_dir))

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            first_session = json.loads(first.stdout)["session"]
            second_session = json.loads(second.stdout)["session"]
            self.assertNotEqual(first_session["id"], second_session["id"])
            self.assertEqual(second_session["project"], str(Path(project_dir).resolve()))

            explicit = self.run_agent("--json", "--session", first_session["id"], "qual", "seu", "nome?", env=env, cwd=Path(project_dir))
            self.assertEqual(explicit.returncode, 0, explicit.stderr)
            self.assertEqual(json.loads(explicit.stdout)["session"]["id"], first_session["id"])

    def test_session_metadata_redacts_json_style_secret_assignments(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            result = self.run_agent("--json", '{"password":"abc123","note":"analise incidente"}', env=env)

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertNotIn("abc123", result.stdout)
            payload = json.loads(result.stdout)
            messages_path = Path(payload["session"]["path"]) / "messages.jsonl"
            self.assertNotIn("abc123", messages_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
