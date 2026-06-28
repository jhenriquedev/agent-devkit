#!/usr/bin/env python3
"""Wave 1 contracts for local Agent DevKit home and memory."""

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


class AgenticWave1ContractsTest(unittest.TestCase):
    def run_agent(self, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        process_env = os.environ | env
        return subprocess.run(
            [sys.executable, str(AGENT), *args],
            cwd=ROOT,
            env=process_env,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CLI_TIMEOUT_SECONDS,
        )

    def test_memory_path_creates_local_home_skeleton_with_ai_devkit_env(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent devkit home ") as tmpdir:
            home = Path(tmpdir)
            result = self.run_agent("memory", "path", "--json", env={"AI_DEVKIT_CONFIG_HOME": str(home)})

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["kind"], "memory-path")
            self.assertEqual(Path(payload["home"]), home.resolve() / "memory")
            for name in ("bin", "config", "memory", "sessions", "tasks", "audit", "cache", "logs", "state"):
                self.assertTrue((home / name).is_dir(), name)
            files = {item["name"]: Path(item["path"]) for item in payload["files"]}
            for name in ("profile.md", "personality.md", "preferences.md", "projects.md", "routines.md", "napkin.md"):
                self.assertIn(name, files)
                self.assertTrue(files[name].is_file(), name)

    def test_default_home_uses_agent_devkit_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            result = self.run_agent(
                "memory",
                "path",
                "--json",
                env={
                    "HOME": str(home),
                    "PATH": os.environ.get("PATH", ""),
                    "AGENT_DEVKIT_HOME": "",
                    "AI_DEVKIT_CONFIG_HOME": "",
                    "AIKIT_CONFIG_HOME": "",
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(Path(payload["home"]), (home / ".agent-devkit" / "memory").resolve())
            self.assertTrue((home / ".agent-devkit" / "memory").is_dir())
            self.assertFalse((home / ".ai-devkit").exists())

    def test_default_home_keeps_existing_ai_devkit_directory_as_legacy_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            legacy = home / ".ai-devkit"
            legacy.mkdir()
            result = self.run_agent(
                "memory",
                "path",
                "--json",
                env={
                    "HOME": str(home),
                    "PATH": os.environ.get("PATH", ""),
                    "AGENT_DEVKIT_HOME": "",
                    "AI_DEVKIT_CONFIG_HOME": "",
                    "AIKIT_CONFIG_HOME": "",
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(Path(payload["home"]), (legacy / "memory").resolve())
            self.assertFalse((home / ".agent-devkit").exists())

    def test_memory_path_keeps_legacy_aikit_config_home_compatibility(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            result = self.run_agent("memory", "path", "--json", env={"AIKIT_CONFIG_HOME": str(home)})

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(Path(payload["home"]), home.resolve() / "memory")

    def test_ai_devkit_config_home_takes_precedence_over_legacy_home(self) -> None:
        with tempfile.TemporaryDirectory() as preferred, tempfile.TemporaryDirectory() as legacy:
            result = self.run_agent(
                "memory",
                "path",
                "--json",
                env={
                    "AI_DEVKIT_CONFIG_HOME": preferred,
                    "AIKIT_CONFIG_HOME": legacy,
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(Path(payload["home"]), Path(preferred).resolve() / "memory")
            self.assertFalse((Path(legacy) / "memory").exists())

    def test_agent_devkit_home_takes_precedence_over_legacy_envs(self) -> None:
        with tempfile.TemporaryDirectory() as canonical, tempfile.TemporaryDirectory() as ai_home, tempfile.TemporaryDirectory() as aikit_home:
            result = self.run_agent(
                "memory",
                "path",
                "--json",
                env={
                    "AGENT_DEVKIT_HOME": canonical,
                    "AI_DEVKIT_CONFIG_HOME": ai_home,
                    "AIKIT_CONFIG_HOME": aikit_home,
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(Path(payload["home"]), Path(canonical).resolve() / "memory")
            self.assertFalse((Path(ai_home) / "memory").exists())
            self.assertFalse((Path(aikit_home) / "memory").exists())

    def test_memory_show_is_idempotent_and_preserves_existing_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            env = {"AI_DEVKIT_CONFIG_HOME": str(home)}
            first = self.run_agent("memory", "show", "--json", env=env)
            profile = home / "memory" / "profile.md"
            profile.write_text("# Profile\n\ncustom content\n", encoding="utf-8")
            second = self.run_agent("memory", "show", "--json", env=env)

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(profile.read_text(encoding="utf-8"), "# Profile\n\ncustom content\n")
            payload = json.loads(second.stdout)
            self.assertEqual(payload["memory_home"], str(home.resolve() / "memory"))
            self.assertTrue(any(item["name"] == "profile.md" for item in payload["files"]))

    def test_recorded_prompt_usage_redacts_common_secret_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            env = {"AI_DEVKIT_CONFIG_HOME": str(home), "PATH": os.environ.get("PATH", "")}
            fixture = home / "card-9900.json"
            fixture.write_text(
                json.dumps(
                    {
                        "work_item": {
                            "id": 9900,
                            "work_item_type": "Bug",
                            "title": "Falha",
                            "state": "Active",
                            "board_column": "Doing",
                            "created_date": "2026-06-27T10:00:00Z",
                            "changed_date": "2026-06-27T11:00:00Z",
                            "assigned_to": "Equipe",
                            "tags": [],
                            "description": "Erro",
                            "acceptance_criteria": "",
                            "url": "https://example.invalid/9900",
                        },
                        "comments": {"comments": []},
                    }
                ),
                encoding="utf-8",
            )
            fake_codex = home / "codex"
            fake_codex.write_text("#!/usr/bin/env sh\nprintf '%s\\n' 'REVIEW OK'\n", encoding="utf-8")
            fake_codex.chmod(0o755)

            configure = self.run_agent(
                "source",
                "add",
                "azure-fixture",
                "--provider",
                "azure-devops",
                "--config",
                "project=Sustentacao",
                "--config",
                f"fixture={fixture}",
                "--default-for",
                "card",
                "--json",
                env=env,
            )
            reviewer = self.run_agent(
                "llm",
                "configure",
                "codex-cli",
                "--command",
                str(fake_codex),
                "--json",
                env=env,
            )
            result = self.run_agent(
                "--json",
                "analise o card 9900 com token=sk-1234567890abcdef",
                env=env,
            )
            memory = self.run_agent("memory", "show", "--json", env=env)

            self.assertEqual(configure.returncode, 0, configure.stderr)
            self.assertEqual(reviewer.returncode, 0, reviewer.stderr)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(memory.returncode, 0, memory.stderr)
            payload = json.loads(memory.stdout)
            prompt_keys = " ".join(item["key"] for item in payload["usage"]["prompts"])
            self.assertIn("[redacted_secret]", prompt_keys)
            self.assertNotIn("sk-1234567890abcdef", prompt_keys)

    def test_napkin_paths_sanitize_agent_and_source_segments(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            result = self.run_agent(
                "memory",
                "show",
                "--agent",
                "../bad agent",
                "--source",
                "../bad source",
                "--json",
                env={"AI_DEVKIT_CONFIG_HOME": str(home)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            napkin_paths = [item["path"] for item in payload["napkin"]["paths"]]
            self.assertTrue(any("agents/bad-agent/napkin.md" in path for path in napkin_paths))
            self.assertTrue(any("sources/bad-source/napkin.md" in path for path in napkin_paths))
            self.assertFalse(any("../bad" in path for path in napkin_paths))


if __name__ == "__main__":
    unittest.main()
