#!/usr/bin/env python3
"""Wave 4 contracts for LLM routing and toolchain setup."""

from __future__ import annotations

import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cli.aikit.toolchain import install_toolchain, is_executable_install_command, setup_plan


AGENT = ROOT / "agent"
CLI_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_CLI_TIMEOUT_SECONDS", "60"))


class OpenAiFailingHandler(http.server.BaseHTTPRequestHandler):
    status_code = 500
    body = {"error": {"message": "temporary backend failure"}}

    def do_POST(self) -> None:  # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length", "0")))
        body = json.dumps(self.body).encode("utf-8")
        self.send_response(self.status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


class OpenAiPolicyHandler(OpenAiFailingHandler):
    status_code = 403
    body = {"error": {"message": "policy violation", "type": "content_policy"}}


class AnthropicOkHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length", "0")))
        body = json.dumps({"content": [{"type": "text", "text": "fallback anthropic response"}]}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


class AgenticWave4ContractsTest(unittest.TestCase):
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

    def server(self, handler: type[http.server.BaseHTTPRequestHandler]) -> tuple[http.server.HTTPServer, str]:
        server = http.server.HTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        return server, f"http://{host}:{port}/v1"

    def configure_openai_and_anthropic(self, env: dict[str, str], openai_url: str, anthropic_url: str) -> None:
        openai = self.run_agent(
            "llm",
            "configure",
            "openai",
            "--api-key-env",
            "TEST_OPENAI_API_KEY",
            "--base-url",
            openai_url,
            "--model",
            "fake-openai",
            "--set-default",
            "--json",
            env=env,
        )
        anthropic = self.run_agent(
            "llm",
            "configure",
            "anthropic",
            "--api-key-env",
            "TEST_ANTHROPIC_API_KEY",
            "--base-url",
            anthropic_url,
            "--model",
            "fake-anthropic",
            "--json",
            env=env,
        )
        self.assertEqual(openai.returncode, 0, openai.stderr)
        self.assertEqual(anthropic.returncode, 0, anthropic.stderr)

    def test_technical_backend_failure_falls_back_to_next_configured_llm(self) -> None:
        failing_openai, openai_url = self.server(OpenAiFailingHandler)
        anthropic, anthropic_url = self.server(AnthropicOkHandler)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                env = {
                    "AI_DEVKIT_CONFIG_HOME": tmpdir,
                    "TEST_OPENAI_API_KEY": "openai-secret",
                    "TEST_ANTHROPIC_API_KEY": "anthropic-secret",
                }
                self.configure_openai_and_anthropic(env, openai_url, anthropic_url)
                result = self.run_agent("--json", "analise", "este", "incidente", env=env)
        finally:
            failing_openai.shutdown()
            failing_openai.server_close()
            anthropic.shutdown()
            anthropic.server_close()

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["llm_backend"], "anthropic")
        self.assertTrue(payload["llm_fallback_used"])
        self.assertEqual([item["id"] for item in payload["llm_backend_attempts"]], ["openai", "anthropic"])
        self.assertNotIn("openai-secret", result.stdout)
        self.assertNotIn("anthropic-secret", result.stdout)

    def test_policy_error_does_not_fallback_to_secondary_llm(self) -> None:
        policy_openai, openai_url = self.server(OpenAiPolicyHandler)
        anthropic, anthropic_url = self.server(AnthropicOkHandler)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                env = {
                    "AI_DEVKIT_CONFIG_HOME": tmpdir,
                    "TEST_OPENAI_API_KEY": "openai-secret",
                    "TEST_ANTHROPIC_API_KEY": "anthropic-secret",
                }
                self.configure_openai_and_anthropic(env, openai_url, anthropic_url)
                result = self.run_agent("--json", "analise", "este", "incidente", env=env)
        finally:
            policy_openai.shutdown()
            policy_openai.server_close()
            anthropic.shutdown()
            anthropic.server_close()

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "failed")
        self.assertTrue(payload["llm_policy_error"])
        self.assertEqual([item["id"] for item in payload["llm_backend_attempts"]], ["openai"])

    def test_no_llm_fallback_blocks_secondary_attempt(self) -> None:
        failing_openai, openai_url = self.server(OpenAiFailingHandler)
        anthropic, anthropic_url = self.server(AnthropicOkHandler)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                env = {
                    "AI_DEVKIT_CONFIG_HOME": tmpdir,
                    "TEST_OPENAI_API_KEY": "openai-secret",
                    "TEST_ANTHROPIC_API_KEY": "anthropic-secret",
                }
                self.configure_openai_and_anthropic(env, openai_url, anthropic_url)
                result = self.run_agent("--json", "--no-llm-fallback", "analise", "este", "incidente", env=env)
        finally:
            failing_openai.shutdown()
            failing_openai.server_close()
            anthropic.shutdown()
            anthropic.server_close()

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["llm_fallback_enabled"])
        self.assertEqual([item["id"] for item in payload["llm_backend_attempts"]], ["openai"])

    def test_llm_preference_show_and_set_primary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            set_result = self.run_agent("llm", "preference", "set", "--primary", "openai", "--order", "openai,anthropic", "--json", env=env)
            reorder_result = self.run_agent("llm", "preference", "reorder", "anthropic,openai", "--json", env=env)
            show_result = self.run_agent("llm", "preference", "show", "--json", env=env)

            self.assertEqual(set_result.returncode, 0, set_result.stderr)
            self.assertEqual(reorder_result.returncode, 0, reorder_result.stderr)
            self.assertEqual(show_result.returncode, 0, show_result.stderr)
            payload = json.loads(show_result.stdout)
            self.assertEqual(payload["kind"], "llm-preference")
            self.assertEqual(payload["primary"], "openai")
            self.assertEqual(payload["order"][:2], ["openai", "anthropic"])
            reorder_payload = json.loads(reorder_result.stdout)
            self.assertEqual(reorder_payload["order"][:2], ["openai", "anthropic"])
            config_text = (Path(tmpdir) / "config.json").read_text(encoding="utf-8")
            self.assertNotIn("sk-", config_text)

    def test_toolchain_and_setup_commands_are_plan_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            listing = self.run_agent("toolchain", "list", "--json", env=env)
            doctor = self.run_agent("toolchain", "doctor", "gh-cli", "--json", env=env)
            install = self.run_agent("toolchain", "install", "gh-cli", "--dry-run", "--json", env=env)
            setup = self.run_agent("setup", "--dry-run", "--json", env=env)

            self.assertEqual(listing.returncode, 0, listing.stderr)
            self.assertEqual(doctor.returncode, 0, doctor.stderr)
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertEqual(setup.returncode, 0, setup.stderr)
            self.assertEqual(json.loads(listing.stdout)["kind"], "toolchain")
            self.assertEqual(json.loads(doctor.stdout)["kind"], "toolchain-doctor")
            install_payload = json.loads(install.stdout)
            self.assertEqual(install_payload["kind"], "toolchain-install")
            self.assertTrue(install_payload["dry_run"])
            self.assertEqual(json.loads(setup.stdout)["kind"], "setup")

    def test_setup_yes_uses_installer_but_skips_already_installed_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tooling = root / "tooling"
            tooling.mkdir()
            (tooling / "toolchain.yaml").write_text(
                "\n".join(
                    [
                        "version: 1",
                        "tools:",
                        "  python:",
                        "    label: Python",
                        "    command: python3",
                        "    required: true",
                        "    install:",
                        "      darwin: brew install python",
                        "      linux: Use your distro package manager.",
                        "      windows: winget install Python.Python.3.12",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            payload = setup_plan(root, dry_run=False, yes=True)

            self.assertEqual(payload["kind"], "setup")
            self.assertEqual(payload["install"]["kind"], "toolchain-install")
            self.assertTrue(payload["install"]["yes"])
            self.assertEqual(payload["install"]["executed"][0]["status"], "already-installed")

    def test_manual_install_instructions_are_not_executable_commands(self) -> None:
        self.assertFalse(is_executable_install_command("Use your distro package manager."))
        self.assertFalse(is_executable_install_command("See https://example.test/install"))
        self.assertFalse(is_executable_install_command("Configure the official Figma MCP integration in your host app."))
        self.assertTrue(is_executable_install_command("npm install -g @openai/codex"))

    def test_install_output_redacts_environment_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tooling = root / "tooling"
            tooling.mkdir()
            (tooling / "toolchain.yaml").write_text(
                "\n".join(
                    [
                        "version: 1",
                        "tools:",
                        "  fake-secret-tool:",
                        "    label: Fake Secret Tool",
                        "    command: definitely-not-installed-agent-devkit-tool",
                        "    required: false",
                        "    install:",
                        "      darwin: python3 -c 'import os; print(os.environ[\"TEST_SECRET_TOKEN\"])'",
                        "      linux: python3 -c 'import os; print(os.environ[\"TEST_SECRET_TOKEN\"])'",
                        "      windows: python -c \"import os; print(os.environ['TEST_SECRET_TOKEN'])\"",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            old_secret = os.environ.get("TEST_SECRET_TOKEN")
            os.environ["TEST_SECRET_TOKEN"] = "secret-output-value"
            try:
                payload = install_toolchain(root, "fake-secret-tool", dry_run=False, yes=True)
            finally:
                if old_secret is None:
                    os.environ.pop("TEST_SECRET_TOKEN", None)
                else:
                    os.environ["TEST_SECRET_TOKEN"] = old_secret

            self.assertEqual(payload["executed"][0]["status"], "installed")
            self.assertIn("[REDACTED]", payload["executed"][0]["stdout"])
            self.assertNotIn("secret-output-value", json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
