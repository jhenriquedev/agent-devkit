#!/usr/bin/env python3
"""Tests for native AI DevKit plugin scaffolds."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"


class AiDevKitPluginsTest(unittest.TestCase):
    def test_codex_plugin_manifest_and_router_skill(self) -> None:
        plugin = PLUGINS / "codex-ai-devkit"
        manifest = json.loads((plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["id"], "codex-ai-devkit")
        self.assertEqual(manifest["runtime"]["command"], "agent")
        self.assertEqual(manifest["skills"][0]["id"], "ai-devkit-router")
        self.assertTrue((plugin / manifest["skills"][0]["path"]).exists())
        self.assertTrue((plugin / "scripts" / "doctor.py").exists())
        self.assertTrue((plugin / "scripts" / "run-capability.py").exists())

        skill = (plugin / "skills" / "ai-devkit-router" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("agent", skill)
        self.assertIn("requires.providers", skill)
        self.assertIn("fallback", skill)

    def test_claude_plugin_manifest_commands_and_router_skill(self) -> None:
        plugin = PLUGINS / "claude-code-ai-devkit"
        manifest = json.loads((plugin / "plugin.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["id"], "claude-code-ai-devkit")
        self.assertEqual(manifest["runtime"]["command"], "agent")
        self.assertEqual(manifest["skills"][0]["id"], "ai-devkit-router")
        for command in ("devkit-setup.md", "devkit-doctor.md", "devkit-provider.md", "devkit-run.md"):
            self.assertTrue((plugin / "commands" / command).exists())

        skill = (plugin / "skills" / "ai-devkit-router" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("agent run", skill)
        self.assertIn("provider configure", skill)
        self.assertIn("agent-devkit-db-analyst", skill)

    def test_claude_plugin_subagents_are_scoped_and_conservative(self) -> None:
        plugin = PLUGINS / "claude-code-ai-devkit"
        agents_dir = plugin / "agents"
        expected = {
            "agent-devkit-repo-explorer.md",
            "agent-devkit-db-analyst.md",
            "agent-devkit-pr-reviewer.md",
            "agent-devkit-support-triage.md",
            "agent-devkit-execution-reviewer.md",
        }

        self.assertTrue(agents_dir.is_dir())
        self.assertFalse(expected - {path.name for path in agents_dir.glob("*.md")})
        for name in expected:
            text = (agents_dir / name).read_text(encoding="utf-8")
            with self.subTest(subagent=name):
                self.assertTrue(text.startswith("---\n"))
                self.assertIn("name: agent-devkit-", text)
                self.assertIn("tools:", text)
                self.assertIn("mcp__agent-devkit__capability_run", text)
                self.assertIn("run-capability.py --json", text)
                self.assertIn("write_policy", text)
                self.assertNotIn("permissionMode:", text)
                self.assertNotIn("mcpServers:", text)
                self.assertNotIn("tools: '*'", text)

    def test_claude_desktop_skill_bundle(self) -> None:
        plugin = PLUGINS / "claude-skill-ai-devkit"
        manifest = json.loads((plugin / "plugin.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["id"], "claude-skill-ai-devkit")
        self.assertEqual(manifest["runtime"]["command"], "agent")
        self.assertEqual(manifest["runtime"]["mode"], "skill-only")
        self.assertEqual(manifest["skills"][0]["id"], "ai-devkit")

        skill_path = plugin / manifest["skills"][0]["path"]
        skill = skill_path.read_text(encoding="utf-8")
        self.assertIn("Claude Desktop", skill)
        self.assertIn("agent run", skill)
        for reference in ("routing.md", "providers.md", "sustentacao.md", "infra.md", "desenvolvimento.md", "subagents.md"):
            self.assertTrue((skill_path.parent / "references" / reference).exists())

    def test_plugin_doctor_scripts_delegate_to_aikit(self) -> None:
        for plugin_id in ("codex-ai-devkit", "claude-code-ai-devkit"):
            with self.subTest(plugin=plugin_id):
                result = subprocess.run(
                    [sys.executable, str(PLUGINS / plugin_id / "scripts" / "doctor.py"), "--json"],
                    cwd=ROOT,
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["kind"], "doctor")
                self.assertEqual(payload["status"], "ok")

    def test_plugin_run_script_preserves_provider_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = subprocess.run(
                [
                    sys.executable,
                    str(PLUGINS / "codex-ai-devkit" / "scripts" / "run-capability.py"),
                    "--json",
                    "elasticsearch-log-analyzer",
                    "search-log-events",
                    "--source",
                    "app",
                    "--from",
                    "2026-06-27T00:00:00Z",
                    "--to",
                    "2026-06-27T01:00:00Z",
                ],
                cwd=ROOT,
                env={"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")},
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "partial")
        self.assertEqual(payload["fallback_applied"], "plan_only")
        self.assertEqual(payload["providers"]["missing"], ["elasticsearch"])

    def test_plugin_run_script_accepts_json_flag_after_capability_args(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = subprocess.run(
                [
                    sys.executable,
                    str(PLUGINS / "claude-code-ai-devkit" / "scripts" / "run-capability.py"),
                    "elasticsearch-log-analyzer",
                    "search-log-events",
                    "--source",
                    "app",
                    "--from",
                    "2026-06-27T00:00:00Z",
                    "--to",
                    "2026-06-27T01:00:00Z",
                    "--json",
                ],
                cwd=ROOT,
                env={"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")},
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "run")
        self.assertEqual(payload["status"], "partial")

    def test_installed_plugin_scripts_resolve_runtime_from_project_config(self) -> None:
        with tempfile.TemporaryDirectory() as project_dir, tempfile.TemporaryDirectory() as config_home:
            install = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "agent"),
                    "--json",
                    "install",
                    "project",
                    "--target",
                    project_dir,
                    "--host",
                    "all",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )
            self.assertEqual(install.returncode, 0, install.stderr)

            codex_doctor = subprocess.run(
                [
                    sys.executable,
                    str(Path(project_dir) / ".codex" / "plugins" / "ai-devkit" / "scripts" / "doctor.py"),
                    "--json",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )
            claude_run = subprocess.run(
                [
                    sys.executable,
                    str(Path(project_dir) / ".claude" / "plugins" / "ai-devkit" / "scripts" / "run-capability.py"),
                    "--json",
                    "elasticsearch-log-analyzer",
                    "search-log-events",
                    "--source",
                    "app",
                    "--from",
                    "2026-06-27T00:00:00Z",
                    "--to",
                    "2026-06-27T01:00:00Z",
                ],
                cwd=ROOT,
                env={"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")},
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )

        self.assertEqual(codex_doctor.returncode, 0, codex_doctor.stderr)
        self.assertEqual(json.loads(codex_doctor.stdout)["kind"], "doctor")
        self.assertEqual(claude_run.returncode, 0, claude_run.stderr)
        claude_payload = json.loads(claude_run.stdout)
        self.assertEqual(claude_payload["kind"], "run")
        self.assertEqual(claude_payload["status"], "partial")


if __name__ == "__main__":
    unittest.main()
