#!/usr/bin/env python3
"""Wave 2 contracts for identity, personality, prompts, and aliases."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cli.aikit.identity import enforce_identity_response


AGENT = ROOT / "agent"
CLI_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_CLI_TIMEOUT_SECONDS", "60"))


class AgenticWave2ContractsTest(unittest.TestCase):
    def run_agent(self, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(AGENT), *args],
            cwd=ROOT,
            env=os.environ | env,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CLI_TIMEOUT_SECONDS,
        )

    def test_identity_question_is_answered_locally_without_llm(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_agent("--json", "qual", "seu", "nome?", env={"AI_DEVKIT_CONFIG_HOME": tmpdir})

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["kind"], "agent")
            self.assertEqual(payload["status"], "ok")
            self.assertFalse(payload["requires_llm"])
            self.assertEqual(payload["identity"]["name"], "Agent DevKit")
            self.assertIn("Agent DevKit", payload["response"])
            self.assertNotIn("Claude", payload["response"])

    def test_capabilities_question_is_answered_locally_without_llm(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_agent(
                "--json",
                "o",
                "que",
                "voce",
                "consegue",
                "fazer",
                "aqui",
                env={"AI_DEVKIT_CONFIG_HOME": tmpdir},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["kind"], "agent")
            self.assertEqual(payload["status"], "ok")
            self.assertFalse(payload["requires_llm"])
            self.assertEqual(payload["mode"], "local-capabilities-help")
            self.assertGreaterEqual(payload["catalog"]["agents"], 1)
            self.assertGreaterEqual(payload["catalog"]["capabilities"], 1)
            self.assertIn("onboard", " ".join(payload["next_steps"]))

    def test_personality_edit_changes_public_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            edit = self.run_agent("personality", "edit", "--name", "Jarvis", "--json", env=env)
            identity = self.run_agent("--json", "qual", "seu", "nome?", env=env)
            show = self.run_agent("personality", "show", "--json", env=env)
            reset = self.run_agent("personality", "reset", "--json", env=env)
            after_reset = self.run_agent("--json", "qual", "seu", "nome?", env=env)

            self.assertEqual(edit.returncode, 0, edit.stderr)
            self.assertEqual(identity.returncode, 0, identity.stderr)
            self.assertEqual(show.returncode, 0, show.stderr)
            self.assertEqual(reset.returncode, 0, reset.stderr)
            self.assertEqual(after_reset.returncode, 0, after_reset.stderr)
            show_payload = json.loads(show.stdout)
            self.assertEqual(show_payload["agent_name"], "Jarvis")
            self.assertIsNone(show_payload["user_name"])
            self.assertIsNone(show_payload["language"])
            self.assertIn("Jarvis", json.loads(identity.stdout)["response"])
            self.assertIn("Agent DevKit", json.loads(after_reset.stdout)["response"])

    def test_personality_rename_flag_and_natural_prompt_change_public_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            rename_flag = self.run_agent("personality", "edit", "--rename", "Ianota", "--json", env=env)
            natural = self.run_agent("--json", "mude", "seu", "nome", "para", "ianota10", env=env)
            identity = self.run_agent("--json", "qual", "seu", "nome?", env=env)
            ianota_alias_exists = (Path(tmpdir) / "bin" / "Ianota").is_file()
            natural_alias_exists = (Path(tmpdir) / "bin" / "ianota10").is_file()

            self.assertEqual(rename_flag.returncode, 0, rename_flag.stderr)
            self.assertEqual(natural.returncode, 0, natural.stderr)
            self.assertEqual(identity.returncode, 0, identity.stderr)
            rename_payload = json.loads(rename_flag.stdout)
            self.assertEqual(rename_payload["agent_name"], "Ianota")
            self.assertEqual(rename_payload["alias"]["name"], "Ianota")
            self.assertTrue(ianota_alias_exists)
            natural_payload = json.loads(natural.stdout)
            self.assertFalse(natural_payload["requires_llm"])
            self.assertEqual(natural_payload["action"], "rename")
            self.assertEqual(natural_payload["identity"]["name"], "ianota10")
            self.assertEqual(natural_payload["alias"]["name"], "ianota10")
            self.assertTrue(natural_alias_exists)
            self.assertIn("ianota10", json.loads(identity.stdout)["response"])

    def test_personality_rename_with_spaced_name_creates_safe_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            renamed = self.run_agent("personality", "edit", "--rename", "Meu Assistente", "--json", env=env)
            alias_exists = (Path(tmpdir) / "bin" / "Meu-Assistente").is_file()

        self.assertEqual(renamed.returncode, 0, renamed.stderr)
        payload = json.loads(renamed.stdout)
        self.assertEqual(payload["agent_name"], "Meu Assistente")
        self.assertEqual(payload["alias"]["name"], "Meu-Assistente")
        self.assertTrue(alias_exists)

    def test_alias_path_command_is_confirmation_gated(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir, "PATH": os.environ.get("PATH", "")}
            result = self.run_agent("alias", "path", "--json", env=env)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "alias-path")
        self.assertEqual(payload["status"], "needs-confirmation")
        self.assertFalse(payload["executed"])

    def test_alias_path_yes_updates_posix_shell_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            home = root / "home"
            app_home = root / "app"
            home.mkdir()
            env = {
                "AI_DEVKIT_CONFIG_HOME": str(app_home),
                "HOME": str(home),
                "SHELL": "/bin/zsh",
                "PATH": os.environ.get("PATH", ""),
            }
            result = self.run_agent("alias", "path", "--yes", "--json", env=env)
            profile_text = (home / ".zshrc").read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "updated")
        self.assertTrue(payload["executed"])
        self.assertIn(str(app_home / "bin"), profile_text)

    def test_alias_add_creates_executable_that_preserves_invoked_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir, "PATH": os.environ.get("PATH", "")}
            add = self.run_agent("alias", "add", "jarvis", "--json", env=env)
            alias_path = Path(tmpdir) / "bin" / "jarvis"
            alias_run = subprocess.run(
                [str(alias_path), "--json", "qual", "seu", "nome?"],
                cwd=ROOT,
                env=os.environ | env,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=CLI_TIMEOUT_SECONDS,
            )
            listing = self.run_agent("alias", "list", "--json", env=env)

            self.assertEqual(add.returncode, 0, add.stderr)
            self.assertTrue(alias_path.is_file())
            self.assertEqual(alias_run.returncode, 0, alias_run.stderr)
            self.assertIn("Jarvis", json.loads(alias_run.stdout)["response"])
            self.assertEqual(listing.returncode, 0, listing.stderr)
            self.assertEqual(json.loads(listing.stdout)["items"][0]["name"], "jarvis")

    def test_alias_rejects_reserved_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_agent("alias", "add", "Agent", env={"AI_DEVKIT_CONFIG_HOME": tmpdir})

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("reserved", result.stderr)

    def test_alias_sync_ignores_invalid_config_keys_without_writing_outside_bin(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_dir = home / "config"
            config_dir.mkdir(parents=True)
            (config_dir / "aliases.json").write_text(
                json.dumps({"version": 1, "aliases": {"../escape": {"created_by": "test"}, "jarvis": {"created_by": "test"}}}),
                encoding="utf-8",
            )

            result = self.run_agent("alias", "sync", "--json", env={"AI_DEVKIT_CONFIG_HOME": str(home)})

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["invalid"], ["../escape"])
            self.assertTrue((home / "bin" / "jarvis").exists())
            self.assertFalse((home / "escape").exists())

    def test_personality_edit_cleans_newlines_before_writing_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            result = self.run_agent(
                "personality",
                "edit",
                "--name",
                "Jarvis\n- Tone: injected",
                "--json",
                env={"AI_DEVKIT_CONFIG_HOME": str(home)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["agent_name"], "Jarvis - Tone: injected")
            text = (home / "memory" / "personality.md").read_text(encoding="utf-8")
            self.assertNotIn("\n- Tone: injected\n", text)

    def test_personality_show_hides_setup_questions_after_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            edit = self.run_agent("personality", "edit", "--name", "Jarvis", env=env)
            show = self.run_agent("personality", "show", env=env)
            setup = self.run_agent("setup", "personality", env=env)

            self.assertEqual(edit.returncode, 0, edit.stderr)
            self.assertEqual(show.returncode, 0, show.stderr)
            self.assertEqual(setup.returncode, 0, setup.stderr)
            self.assertNotIn("Setup questions:", show.stdout)
            self.assertIn("Setup questions:", setup.stdout)

    def test_identity_enforcement_rewrites_backend_identity_leak_for_any_prompt(self) -> None:
        response = enforce_identity_response("I'm Claude, an AI from Anthropic.", "explique o incidente", name="Jarvis")

        self.assertEqual(response, "Meu nome e Jarvis.")

    def test_host_cli_prompt_contains_public_identity_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            fake_bin = home / "bin-fixture"
            fake_bin.mkdir()
            capture = home / "capture.txt"
            fake_claude = fake_bin / "claude"
            fake_claude.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env sh",
                        "set -eu",
                        f"printf '%s\\n' \"$@\" > {json.dumps(str(capture))}",
                        "printf '%s\\n' 'ok'",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            fake_claude.chmod(0o755)
            env = {
                "AI_DEVKIT_CONFIG_HOME": str(home),
                "PATH": f"{fake_bin}:{os.environ.get('PATH', '')}",
            }
            configure = self.run_agent("llm", "configure", "claude-code", "--set-default", "--json", env=env)
            result = self.run_agent("--json", "explique", "o", "incidente", env=env)

            self.assertEqual(configure.returncode, 0, configure.stderr)
            self.assertEqual(result.returncode, 0, result.stderr)
            captured = capture.read_text(encoding="utf-8")
            self.assertIn("Voce e Agent DevKit", captured)
            self.assertIn("A LLM conectada e apenas o motor de raciocinio", captured)


if __name__ == "__main__":
    unittest.main()
