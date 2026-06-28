#!/usr/bin/env python3
"""End-to-end tests for clean AI DevKit runtime installs."""

from __future__ import annotations

import json
import http.server
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AIKIT = ROOT / "aikit"
CLI_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_CLI_TIMEOUT_SECONDS", "60"))


class FakeOpenAiHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API.
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        payload = {"choices": [{"message": {"content": "fake openai-compatible response"}}]}
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


class FakeAnthropicHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API.
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        payload = {"content": [{"type": "text", "text": "fake anthropic response"}]}
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


class AikitCleanInstallE2ETest(unittest.TestCase):
    def run_cli(
        self,
        *args: str,
        config_home: Path,
        install_home: Path,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = {
            "AIKIT_CONFIG_HOME": str(config_home),
            "AIKIT_INSTALL_HOME": str(install_home),
            "PATH": os.environ.get("PATH", ""),
        }
        env.update(extra_env or {})
        return subprocess.run(
            [sys.executable, str(AIKIT), *args],
            cwd=ROOT,
            env=env,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CLI_TIMEOUT_SECONDS,
        )

    def fake_server(self, handler: type[http.server.BaseHTTPRequestHandler]) -> tuple[http.server.HTTPServer, str]:
        server = http.server.HTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        return server, f"http://{host}:{port}/v1"

    def write_fake_host_cli(self, directory: Path, name: str, response: str) -> Path:
        path = directory / name
        path.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env sh",
                    "set -eu",
                    f"printf '%s\\n' {json.dumps(response)}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        path.chmod(0o755)
        return path

    def test_clean_project_install_without_credentials_keeps_runtime_usable(self) -> None:
        with (
            tempfile.TemporaryDirectory() as project_dir,
            tempfile.TemporaryDirectory() as config_home,
            tempfile.TemporaryDirectory() as install_home,
        ):
            project = Path(project_dir)
            config = Path(config_home)
            home = Path(install_home)

            install = self.run_cli(
                "--json",
                "install",
                "project",
                "--target",
                str(project),
                "--host",
                "all",
                config_home=config,
                install_home=home,
            )
            doctor = self.run_cli(
                "--json",
                "doctor",
                "--project",
                str(project),
                "--home",
                str(home),
                config_home=config,
                install_home=home,
            )
            agents = self.run_cli("--json", "agents", "list", config_home=config, install_home=home)
            capabilities = self.run_cli(
                "--json",
                "capabilities",
                "list",
                "--agent",
                "elasticsearch-log-analyzer",
                config_home=config,
                install_home=home,
            )
            no_llm = self.run_cli(
                "--json",
                "agent",
                "analise esse incidente no Elasticsearch",
                config_home=config,
                install_home=home,
            )
            fallback = self.run_cli(
                "--json",
                "run",
                "elasticsearch-log-analyzer",
                "search-log-events",
                "--source",
                "app-logs",
                "--from",
                "2026-06-27T00:00:00Z",
                "--to",
                "2026-06-27T01:00:00Z",
                config_home=config,
                install_home=home,
            )
            installed_doctor = subprocess.run(
                [
                    sys.executable,
                    str(project / ".codex" / "plugins" / "ai-devkit" / "scripts" / "doctor.py"),
                    "--json",
                ],
                cwd=ROOT,
                env={
                    "AIKIT_CONFIG_HOME": str(config),
                    "AIKIT_INSTALL_HOME": str(home),
                    "PATH": os.environ.get("PATH", ""),
                },
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=CLI_TIMEOUT_SECONDS,
            )
            installed_run = subprocess.run(
                [
                    sys.executable,
                    str(project / ".claude" / "plugins" / "ai-devkit" / "scripts" / "run-capability.py"),
                    "--json",
                    "elasticsearch-log-analyzer",
                    "search-log-events",
                    "--source",
                    "app-logs",
                    "--from",
                    "2026-06-27T00:00:00Z",
                    "--to",
                    "2026-06-27T01:00:00Z",
                ],
                cwd=ROOT,
                env={
                    "AIKIT_CONFIG_HOME": str(config),
                    "AIKIT_INSTALL_HOME": str(home),
                    "PATH": os.environ.get("PATH", ""),
                },
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=CLI_TIMEOUT_SECONDS,
            )
            project_lock_exists = Path(json.loads(install.stdout)["lock_path"]).exists()
            codex_plugin_exists = (project / ".codex" / "plugins" / "ai-devkit").exists()
            claude_plugin_exists = (project / ".claude" / "plugins" / "ai-devkit").exists()

        self.assertEqual(install.returncode, 0, install.stderr)
        install_payload = json.loads(install.stdout)
        self.assertEqual(install_payload["kind"], "install")
        self.assertEqual(install_payload["status"], "installed")
        self.assertFalse(install_payload["stored_secret"])
        self.assertTrue(project_lock_exists)
        self.assertTrue(codex_plugin_exists)
        self.assertTrue(claude_plugin_exists)

        self.assertEqual(doctor.returncode, 0, doctor.stderr)
        doctor_payload = json.loads(doctor.stdout)
        self.assertEqual(doctor_payload["kind"], "doctor")
        self.assertEqual(doctor_payload["status"], "ok")
        self.assertIn(doctor_payload["diagnostics"]["providers"]["status"], {"partial", "missing"})
        self.assertIn(doctor_payload["diagnostics"]["llm"]["status"], {"partial", "missing"})

        self.assertEqual(agents.returncode, 0, agents.stderr)
        agent_ids = {item["id"] for item in json.loads(agents.stdout)["items"]}
        self.assertIn("elasticsearch-log-analyzer", agent_ids)

        self.assertEqual(capabilities.returncode, 0, capabilities.stderr)
        capability_ids = {item["id"].split(".")[-1] for item in json.loads(capabilities.stdout)["items"]}
        self.assertIn("search-log-events", capability_ids)

        self.assertEqual(no_llm.returncode, 2, no_llm.stderr)
        no_llm_payload = json.loads(no_llm.stdout)
        self.assertEqual(no_llm_payload["kind"], "agent")
        self.assertEqual(no_llm_payload["status"], "needs-input")
        self.assertFalse(no_llm_payload.get("requires_llm", False))
        self.assertEqual(no_llm_payload["provider"], "elasticsearch")
        self.assertEqual(no_llm_payload["setup_wizard"]["owner_agent"], "provider-configurator")

        self.assertEqual(fallback.returncode, 0, fallback.stderr)
        fallback_payload = json.loads(fallback.stdout)
        self.assertEqual(fallback_payload["kind"], "run")
        self.assertEqual(fallback_payload["schema_version"], "ai-devkit.run/v1")
        self.assertEqual(fallback_payload["status"], "partial")
        self.assertEqual(fallback_payload["providers"]["missing"], ["elasticsearch"])
        self.assertEqual(fallback_payload["fallback_applied"], "plan_only")

        self.assertEqual(installed_doctor.returncode, 0, installed_doctor.stderr)
        self.assertEqual(json.loads(installed_doctor.stdout)["kind"], "doctor")
        self.assertEqual(installed_run.returncode, 0, installed_run.stderr)
        installed_run_payload = json.loads(installed_run.stdout)
        self.assertEqual(installed_run_payload["kind"], "run")
        self.assertEqual(installed_run_payload["status"], "partial")
        self.assertEqual(installed_run_payload["fallback_applied"], "plan_only")

    def test_fake_provider_env_file_and_fixture_execution_do_not_leak_secrets(self) -> None:
        sentinel = "leak-check-clean-e2e"
        with (
            tempfile.TemporaryDirectory() as config_home,
            tempfile.TemporaryDirectory() as install_home,
            tempfile.TemporaryDirectory() as tmpdir,
        ):
            config = Path(config_home)
            home = Path(install_home)
            tmp = Path(tmpdir)
            env_file = tmp / "elastic.env"
            env_file.write_text(
                "\n".join(
                    [
                        "ELASTICSEARCH_URL=https://elastic.example.com",
                        f"ELASTICSEARCH_API_KEY={sentinel}",
                    ]
                ),
                encoding="utf-8",
            )
            fixture = tmp / "events.json"
            fixture.write_text(
                json.dumps(
                    {
                        "source": "app-logs",
                        "start_time": "2026-06-27T00:00:00Z",
                        "end_time": "2026-06-27T01:00:00Z",
                        "events": [
                            {
                                "timestamp": "2026-06-27T00:05:00Z",
                                "service": "checkout",
                                "level": "ERROR",
                                "trace_id": "trace-clean-e2e",
                                "message": "payment failed",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            card_fixture = tmp / "card.json"
            card_fixture.write_text(
                json.dumps(
                    {
                        "work_item": {
                            "id": 7710,
                            "work_item_type": "Bug",
                            "title": "Falha no login",
                            "state": "Active",
                            "description": "Cliente reportou erro intermitente.",
                            "acceptance_criteria": "Corrigir login e validar regressao.",
                            "assigned_to": "dev@example.com",
                            "tags": ["sustentacao"],
                        },
                        "comments": {
                            "comments": [
                                {
                                    "author": "Analista",
                                    "created_at": "2026-06-27T10:00:00Z",
                                    "text": "Validar logs do checkout.",
                                }
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )

            configure = self.run_cli(
                "--json",
                "provider",
                "configure",
                "elasticsearch",
                "--env-file",
                str(env_file),
                config_home=config,
                install_home=home,
            )
            elastic_run = self.run_cli(
                "--json",
                "run",
                "elasticsearch-log-analyzer",
                "search-log-events",
                "--fixture",
                str(fixture),
                config_home=config,
                install_home=home,
            )
            azure_fixture_run = self.run_cli(
                "--json",
                "run",
                "azure-devops-orchestrator",
                "read-card",
                "--fixture",
                str(card_fixture),
                "--include-comments",
                config_home=config,
                install_home=home,
            )
            config_text = (config / "config.json").read_text(encoding="utf-8")

        self.assertEqual(configure.returncode, 0, configure.stderr)
        configure_payload = json.loads(configure.stdout)
        self.assertEqual(configure_payload["status"], "configured")
        self.assertFalse(configure_payload["stored_secret"])
        self.assertNotIn(sentinel, configure.stdout)
        self.assertNotIn(sentinel, configure.stderr)
        self.assertNotIn(sentinel, config_text)
        self.assertIn("env-file:", config_text)

        self.assertEqual(elastic_run.returncode, 0, elastic_run.stderr)
        elastic_payload = json.loads(elastic_run.stdout)
        self.assertEqual(elastic_payload["status"], "ok")
        self.assertEqual(elastic_payload["providers"]["used"], ["elasticsearch"])
        self.assertIn("payment failed", elastic_payload["stdout"])
        self.assertNotIn(sentinel, elastic_run.stdout)
        self.assertNotIn(sentinel, elastic_run.stderr)

        self.assertEqual(azure_fixture_run.returncode, 0, azure_fixture_run.stderr)
        azure_payload = json.loads(azure_fixture_run.stdout)
        self.assertEqual(azure_payload["status"], "ok")
        self.assertEqual(azure_payload["agent_id"], "azure-devops-orchestrator")
        self.assertEqual(azure_payload["capability_id"], "read-card")
        self.assertIn("# Card Analysis", azure_payload["stdout"])
        self.assertIn("Falha no login", azure_payload["stdout"])
        self.assertNotIn(sentinel, azure_fixture_run.stdout)
        self.assertNotIn(sentinel, azure_fixture_run.stderr)

    def test_llm_backends_execute_offline_with_fake_api_and_host_cli(self) -> None:
        openai_server, openai_base_url = self.fake_server(FakeOpenAiHandler)
        anthropic_server, anthropic_base_url = self.fake_server(FakeAnthropicHandler)
        try:
            with (
                tempfile.TemporaryDirectory() as config_home,
                tempfile.TemporaryDirectory() as install_home,
                tempfile.TemporaryDirectory() as bin_dir,
            ):
                config = Path(config_home)
                home = Path(install_home)
                fake_bin = Path(bin_dir)
                fake_codex = self.write_fake_host_cli(fake_bin, "codex", "fake codex response")
                fake_claude = self.write_fake_host_cli(fake_bin, "claude", "fake claude response")
                env = {
                    "OPENAI_E2E_KEY": "leak-check-openai-e2e",
                    "ANTHROPIC_E2E_KEY": "leak-check-anthropic-e2e",
                    "OPENROUTER_E2E_KEY": "leak-check-openrouter-e2e",
                    "PATH": f"{fake_bin}:{os.environ.get('PATH', '')}",
                }
                cases = [
                    (
                        "openai",
                        [
                            "--api-key-env",
                            "OPENAI_E2E_KEY",
                            "--base-url",
                            openai_base_url,
                            "--model",
                            "fake-openai",
                        ],
                        "fake openai-compatible response",
                    ),
                    (
                        "anthropic",
                        [
                            "--api-key-env",
                            "ANTHROPIC_E2E_KEY",
                            "--base-url",
                            anthropic_base_url,
                            "--model",
                            "fake-claude",
                        ],
                        "fake anthropic response",
                    ),
                    (
                        "openrouter",
                        [
                            "--api-key-env",
                            "OPENROUTER_E2E_KEY",
                            "--base-url",
                            openai_base_url,
                            "--model",
                            "fake/openrouter",
                        ],
                        "fake openai-compatible response",
                    ),
                    (
                        "ollama",
                        ["--base-url", openai_base_url, "--model", "fake-ollama"],
                        "fake openai-compatible response",
                    ),
                    (
                        "codex-cli",
                        ["--command", str(fake_codex)],
                        "fake codex response",
                    ),
                    (
                        "claude-code",
                        ["--command", str(fake_claude)],
                        "fake claude response",
                    ),
                ]

                results = []
                for backend, args, expected in cases:
                    with self.subTest(backend=backend):
                        configure = self.run_cli(
                            "--json",
                            "llm",
                            "configure",
                            backend,
                            *args,
                            "--set-default",
                            config_home=config,
                            install_home=home,
                            extra_env=env,
                        )
                        run = self.run_cli(
                            "--json",
                            "agent",
                            "analise esse incidente",
                            config_home=config,
                            install_home=home,
                            extra_env=env,
                        )
                        self.assertEqual(configure.returncode, 0, configure.stderr)
                        self.assertEqual(run.returncode, 0, run.stderr)
                        payload = json.loads(run.stdout)
                        self.assertEqual(payload["status"], "ok")
                        self.assertEqual(payload["llm_backend"], backend)
                        self.assertEqual(payload["response"], expected)
                        self.assertNotIn("leak-check-", run.stdout)
                        self.assertNotIn("leak-check-", configure.stdout)
                        results.append(backend)
        finally:
            openai_server.shutdown()
            openai_server.server_close()
            anthropic_server.shutdown()
            anthropic_server.server_close()

        self.assertEqual(
            results,
            ["openai", "anthropic", "openrouter", "ollama", "codex-cli", "claude-code"],
        )


if __name__ == "__main__":
    unittest.main()
