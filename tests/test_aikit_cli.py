#!/usr/bin/env python3
"""Tests for the public aikit CLI entrypoint."""

from __future__ import annotations

import json
import os
import http.server
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cli.aikit.credentials import resolve_provider_credentials
from cli.aikit.fallback import evaluate_provider_requirements
from cli.aikit.guardrails import evaluate_execution_guardrails
from cli.aikit.lock import read_simple_lock
from cli.aikit.sources import source_env


AIKIT = ROOT / "aikit"
AI_DEVKIT = ROOT / "ai-devkit"
AGENT = ROOT / "agent"
CLI_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_CLI_TIMEOUT_SECONDS", "60"))
REQUIRED_CORE_AGENTS = {
    "azure-devops-orchestrator",
    "aws-cloudwatch-log-analyzer",
    "database-change-operator",
    "elasticsearch-log-analyzer",
    "execution-reviewer",
    "github-pr-reviewer",
    "local-llm-operator",
    "n1-support-agent",
    "n2-support-agent",
    "postgres-data-analyzer",
    "provider-configurator",
    "sqlserver-data-analyzer",
    "task-orchestrator",
    "topdesk-orchestrator",
}
REQUIRED_CORE_CAPABILITIES = {
    "azure-devops-orchestrator.read-card",
    "execution-reviewer.review-final-output",
    "github-pr-reviewer.review-pr-diff",
    "local-llm-operator.select-local-worker",
    "provider-configurator.configure-provider-source",
    "task-orchestrator.plan-task",
}


class FakeOpenAiHandler(http.server.BaseHTTPRequestHandler):
    response_text = "Use agent run <agent> <capability> para execucao deterministica."

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API.
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        payload = {
            "choices": [
                {
                    "message": {
                        "content": self.response_text,
                    }
                }
            ]
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


class FakeAnthropicHandler(http.server.BaseHTTPRequestHandler):
    response_text = "Use agent run <agent> <capability> com Anthropic fake."

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API.
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        payload = {
            "content": [
                {
                    "type": "text",
                    "text": self.response_text,
                }
            ]
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


class AikitCliTest(unittest.TestCase):
    def run_cli(
        self,
        *args: str,
        env: dict[str, str] | None = None,
        replace_env: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        if replace_env:
            process_env = env or {}
        else:
            process_env = os.environ | (env or {})
        return subprocess.run(
            [sys.executable, str(AIKIT), *args],
            cwd=ROOT,
            env=process_env,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CLI_TIMEOUT_SECONDS,
        )

    def run_agent(
        self,
        *args: str,
        env: dict[str, str] | None = None,
        replace_env: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        if replace_env:
            process_env = env or {}
        else:
            process_env = os.environ | (env or {})
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

    def fake_llm_server(self) -> tuple[http.server.HTTPServer, str]:
        server = http.server.HTTPServer(("127.0.0.1", 0), FakeOpenAiHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        return server, f"http://{host}:{port}/v1"

    def fake_anthropic_server(self) -> tuple[http.server.HTTPServer, str]:
        server = http.server.HTTPServer(("127.0.0.1", 0), FakeAnthropicHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        return server, f"http://{host}:{port}/v1"

    def write_fake_host_cli(self, directory: str, name: str, response: str) -> Path:
        path = Path(directory) / name
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

    def write_card_fixture(self, path: Path, *, card_id: int) -> Path:
        path.write_text(
            json.dumps(
                {
                    "work_item": {
                        "id": card_id,
                        "work_item_type": "Bug",
                        "title": f"Falha no card {card_id}",
                        "state": "Active",
                        "board_column": "Doing",
                        "created_date": "2026-06-27T10:00:00Z",
                        "changed_date": "2026-06-27T11:00:00Z",
                        "assigned_to": "Equipe Sustentacao",
                        "tags": ["incidente"],
                        "description": "Servico apresenta erro intermitente.",
                        "acceptance_criteria": "Identificar causa raiz e registrar plano.",
                        "url": f"https://dev.azure.com/example/project/_workitems/edit/{card_id}",
                    },
                    "comments": {
                        "comments": [
                            {
                                "author": "Analista",
                                "created_at": "2026-06-27T11:10:00Z",
                                "text": "Favor avaliar impacto.",
                            }
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_help_exits_successfully(self) -> None:
        result = self.run_cli("--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AI DevKit CLI", result.stdout)
        self.assertIn("agents", result.stdout)
        self.assertIn("capabilities", result.stdout)
        self.assertIn("agent", result.stdout)
        self.assertIn("doctor", result.stdout)

    def test_version_exits_successfully(self) -> None:
        result = self.run_cli("--version")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("aikit 0.1.7", result.stdout)

    def test_short_version_exits_successfully(self) -> None:
        result = self.run_cli("-v")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("aikit 0.1.7", result.stdout)

    def test_agent_entrypoint_version_uses_agent_program_name(self) -> None:
        result = self.run_agent("--version")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("agent 0.1.7", result.stdout)

    def test_agent_entrypoint_short_version_uses_agent_program_name(self) -> None:
        result = self.run_agent("-v")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("agent 0.1.7", result.stdout)

    def test_agents_list_json(self) -> None:
        result = self.run_cli("agents", "list", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "agents")
        ids = {item["id"] for item in payload["items"]}
        self.assertFalse(REQUIRED_CORE_AGENTS - ids)
        self.assertTrue(all("capabilities" in item for item in payload["items"]))

    def test_capabilities_list_all_json(self) -> None:
        result = self.run_cli("capabilities", "list", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "capabilities")
        self.assertIsNone(payload["agent"])
        capability_ids = {item["id"] for item in payload["items"]}
        self.assertFalse(REQUIRED_CORE_CAPABILITIES - capability_ids)
        self.assertTrue(all("agent" in item for item in payload["items"]))

    def test_capabilities_list_filter_agent_json(self) -> None:
        result = self.run_cli("capabilities", "list", "--agent", "presentation-deck-builder", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["agent"], "presentation-deck-builder")
        capabilities = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertIn("generate-deck-from-template", capabilities)
        self.assertIn("register-template", capabilities)

    def test_capabilities_legacy_agent_argument_still_works(self) -> None:
        result = self.run_cli("--json", "capabilities", "presentation-deck-builder")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["agent"], "presentation-deck-builder")
        capabilities = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertIn("generate-deck-from-template", capabilities)

    def test_doctor_json(self) -> None:
        result = self.run_cli("doctor", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "doctor")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["scope"], "auto")
        summary = payload["summary"]
        self.assertGreaterEqual(summary["agents"], len(REQUIRED_CORE_AGENTS))
        self.assertGreaterEqual(summary["capabilities"], summary["agents"])
        self.assertGreater(summary["declared_runners"], 0)
        self.assertLessEqual(summary["declared_runners"], summary["capabilities"])
        self.assertEqual(summary["workflows"], summary["capabilities"])
        self.assertEqual(summary["decision_rules"], summary["capabilities"])

    def test_doctor_json_includes_expanded_diagnostics(self) -> None:
        result = self.run_cli(
            "doctor",
            "--json",
            env={"PATH": os.environ.get("PATH", ""), "OPENAI_API_KEY": "leak-check-openai"},
            replace_env=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["checks"]["agent_command_exists"])
        self.assertTrue(payload["checks"]["aikit_command_exists"])
        self.assertTrue(payload["checks"]["ai_devkit_command_exists"])
        diagnostics = payload["diagnostics"]
        self.assertEqual(diagnostics["runtime"]["status"], "ok")
        self.assertIn("locks", diagnostics)
        self.assertIn("plugins", diagnostics)
        self.assertIn("providers", diagnostics)
        self.assertIn("llm", diagnostics)
        self.assertEqual(diagnostics["providers"]["kind"], "provider-summary")
        self.assertGreaterEqual(diagnostics["providers"]["total"], 1)
        self.assertGreaterEqual(diagnostics["providers"]["missing"], 1)
        self.assertIn(diagnostics["providers"]["status"], {"ok", "partial", "missing"})
        self.assertEqual(diagnostics["llm"]["kind"], "llm-summary")
        self.assertGreaterEqual(diagnostics["llm"]["total"], 1)
        self.assertNotIn("leak-check-openai", result.stdout)

    def test_doctor_scope_project_uses_current_project_when_project_omitted(self) -> None:
        result = self.run_cli("--json", "doctor", "--scope", "project")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "doctor")
        self.assertEqual(payload["scope"], "project")
        self.assertIn("project", payload["locks"])
        self.assertTrue(payload["locks"]["project"]["path"].endswith(".ai-devkit/ai-devkit.lock"))

    def test_doctor_scope_global_ignores_project_lock(self) -> None:
        result = self.run_cli("--json", "doctor", "--scope", "global")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "doctor")
        self.assertEqual(payload["scope"], "global")
        self.assertFalse(payload["locks"]["project"]["exists"])

    def test_doctor_does_not_fail_for_optional_missing_providers_or_llms(self) -> None:
        result = self.run_cli(
            "--json",
            "doctor",
            env={"PATH": os.environ.get("PATH", "")},
            replace_env=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["diagnostics"]["providers"]["status"], "partial")
        self.assertIn(payload["diagnostics"]["llm"]["status"], {"partial", "missing"})
        self.assertFalse(payload["errors"])

    def test_config_migrate_home_dry_run_and_execute(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            legacy = home / ".ai-devkit"
            canonical = home / ".agent-devkit"
            legacy.mkdir()
            (legacy / "config.json").write_text('{"version": 1}\n', encoding="utf-8")
            env = {
                "HOME": str(home),
                "PATH": os.environ.get("PATH", ""),
                "AGENT_DEVKIT_HOME": "",
                "AI_DEVKIT_CONFIG_HOME": "",
                "AIKIT_CONFIG_HOME": "",
            }
            dry_run = self.run_cli("config", "migrate-home", "--dry-run", "--json", env=env, replace_env=True)
            execute = self.run_cli("config", "migrate-home", "--json", env=env, replace_env=True)
            canonical_config_exists = (canonical / "config.json").is_file()
            legacy_exists_after_execute = legacy.exists()
            after = self.run_cli("config", "migrate-home", "--json", env=env, replace_env=True)

        self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
        dry_payload = json.loads(dry_run.stdout)
        self.assertEqual(dry_payload["status"], "planned")
        self.assertEqual(Path(dry_payload["source"]), legacy.resolve())
        self.assertEqual(Path(dry_payload["destination"]), canonical.resolve())
        self.assertFalse(dry_payload["executed"])
        self.assertEqual(execute.returncode, 0, execute.stderr)
        execute_payload = json.loads(execute.stdout)
        self.assertEqual(execute_payload["status"], "migrated")
        self.assertTrue(execute_payload["executed"])
        self.assertTrue(canonical_config_exists)
        self.assertFalse(legacy_exists_after_execute)
        self.assertEqual(after.returncode, 0, after.stderr)
        self.assertEqual(json.loads(after.stdout)["status"], "not-needed")

    def test_doctor_project_validates_installed_plugins(self) -> None:
        with tempfile.TemporaryDirectory() as install_home, tempfile.TemporaryDirectory() as project_dir:
            install = self.run_cli(
                "--json",
                "install",
                "project",
                "--target",
                project_dir,
                "--host",
                "all",
                env={"AIKIT_INSTALL_HOME": install_home, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )
            doctor = self.run_cli(
                "--json",
                "doctor",
                "--project",
                project_dir,
                "--home",
                install_home,
                env={"AIKIT_INSTALL_HOME": install_home, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(install.returncode, 0, install.stderr)
        self.assertEqual(doctor.returncode, 0, doctor.stderr)
        payload = json.loads(doctor.stdout)
        plugins = payload["diagnostics"]["plugins"]
        self.assertEqual(plugins["status"], "ok")
        self.assertTrue(plugins["project"]["codex"]["plugin_exists"])
        self.assertTrue(plugins["project"]["codex"]["skill_exists"])
        self.assertTrue(plugins["project"]["claude-code"]["plugin_exists"])
        self.assertTrue(plugins["project"]["claude-code"]["skill_exists"])
        self.assertTrue(plugins["project"]["claude-code"]["commands_exists"])
        self.assertTrue(plugins["project"]["claude-code"]["agents_exists"])
        self.assertIn("agent-devkit-db-analyst", plugins["project"]["claude-code"]["subagents"])
        self.assertTrue(plugins["project"]["claude-desktop"]["plugin_exists"])
        self.assertTrue(plugins["project"]["claude-desktop"]["skill_exists"])
        self.assertTrue(plugins["project"]["claude-desktop"]["references_exists"])

    def test_doctor_project_reports_missing_plugins_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as project_dir:
            doctor = self.run_cli("--json", "doctor", "--project", project_dir)

        self.assertEqual(doctor.returncode, 0, doctor.stderr)
        payload = json.loads(doctor.stdout)
        plugins = payload["diagnostics"]["plugins"]
        self.assertEqual(plugins["status"], "missing")
        self.assertEqual(plugins["project"]["codex"]["status"], "missing")
        self.assertEqual(plugins["project"]["claude-code"]["status"], "missing")
        self.assertFalse(plugins["project"]["claude-code"]["agents_exists"])
        self.assertEqual(plugins["project"]["claude-desktop"]["status"], "missing")
        self.assertEqual(payload["status"], "ok")

    def test_commands_list_separates_llm_and_deterministic_commands(self) -> None:
        result = self.run_cli("commands", "list", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "commands")
        deterministic = {item["command"] for item in payload["deterministic"]}
        llm = {item["command"] for item in payload["llm"]}
        self.assertIn("run", deterministic)
        self.assertIn("doctor", deterministic)
        self.assertIn("agents", deterministic)
        self.assertIn("architecture", deterministic)
        self.assertIn("commands", deterministic)
        self.assertIn("llm", deterministic)
        self.assertIn("providers", deterministic)
        self.assertIn("provider", deterministic)
        self.assertIn("credential", deterministic)
        self.assertIn("source", deterministic)
        self.assertIn("memory", deterministic)
        self.assertIn("install", deterministic)
        self.assertIn("agent", llm)
        self.assertTrue(all(not item["requires_llm"] for item in payload["deterministic"]))
        self.assertTrue(all(item["requires_llm"] for item in payload["llm"]))

    def test_providers_list_json(self) -> None:
        result = self.run_cli("providers", "list", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "providers")
        ids = {item["id"] for item in payload["items"]}
        self.assertIn("aws", ids)
        self.assertIn("azure-devops", ids)
        self.assertIn("elasticsearch", ids)
        self.assertIn("postgres", ids)
        self.assertIn("sqlserver", ids)
        self.assertIn("topdesk", ids)
        self.assertIn("bpo", ids)
        self.assertIn("figma", ids)
        self.assertIn("technical-http", ids)

    def test_provider_status_does_not_print_secret_values(self) -> None:
        result = self.run_cli(
            "provider",
            "status",
            "azure-devops",
            "--json",
            env={
                "AZURE_DEVOPS_ORG": "example-org",
                "AZURE_DEVOPS_PAT": "secret-value-that-must-not-leak",
            },
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "provider-status")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["items"][0]["id"], "azure-devops")
        self.assertEqual(payload["items"][0]["status"], "ok")
        self.assertIn("AZURE_DEVOPS_ORG", payload["items"][0]["detected_env"])
        self.assertIn("AZURE_DEVOPS_PAT", payload["items"][0]["detected_env"])
        self.assertNotIn("secret-value-that-must-not-leak", result.stdout)

    def test_provider_status_missing_required_fields(self) -> None:
        result = self.run_cli(
            "provider",
            "status",
            "topdesk",
            "--json",
            env={"PATH": os.environ.get("PATH", "")},
            replace_env=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "provider-status")
        self.assertEqual(payload["status"], "missing")
        item = payload["items"][0]
        self.assertEqual(item["id"], "topdesk")
        self.assertIn("TOPDESK_BASE_URL", item["missing_required_fields"])
        self.assertIn("TOPDESK_USERNAME", item["missing_required_fields"])

    def test_provider_status_accepts_alternative_secret_fields(self) -> None:
        cases = [
            (
                "elasticsearch",
                {"ELASTICSEARCH_URL": "https://elastic.example.com", "ELASTICSEARCH_API_KEY": "leak-check-elastic"},
            ),
            (
                "topdesk",
                {
                    "TOPDESK_BASE_URL": "https://topdesk.example.com",
                    "TOPDESK_USERNAME": "agent",
                    "TOPDESK_APP_PASSWORD": "leak-check-topdesk",
                },
            ),
            ("postgres", {"POSTGRES_DB_CONN_STRING": "postgres://user:leak-check-postgres@example/db"}),
            ("sqlserver", {"SQLSERVER_DB_CONN_STRING": "Driver={ODBC};Pwd=leak-check-sqlserver"}),
        ]
        for provider, provider_env in cases:
            with self.subTest(provider=provider):
                result = self.run_cli(
                    "provider",
                    "status",
                    provider,
                    "--json",
                    env={"PATH": os.environ.get("PATH", "")} | provider_env,
                    replace_env=True,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["kind"], "provider-status")
                self.assertEqual(payload["status"], "ok")
                self.assertEqual(payload["items"][0]["status"], "ok")
                self.assertNotIn("leak-check-", result.stdout)

    def test_provider_status_requires_detection_for_secretless_external_method(self) -> None:
        missing = self.run_cli(
            "provider",
            "status",
            "figma",
            "--json",
            env={"PATH": os.environ.get("PATH", "")},
            replace_env=True,
        )
        configured = self.run_cli(
            "provider",
            "status",
            "figma",
            "--json",
            env={
                "PATH": os.environ.get("PATH", ""),
                "FIGMA_MCP_BRIDGE_COMMAND": "codex figma bridge",
            },
            replace_env=True,
        )

        self.assertEqual(missing.returncode, 0, missing.stderr)
        missing_payload = json.loads(missing.stdout)
        self.assertEqual(missing_payload["status"], "missing")
        self.assertEqual(missing_payload["items"][0]["status"], "missing")

        self.assertEqual(configured.returncode, 0, configured.stderr)
        configured_payload = json.loads(configured.stdout)
        self.assertEqual(configured_payload["status"], "ok")
        self.assertEqual(configured_payload["items"][0]["status"], "ok")
        self.assertIn("FIGMA_MCP_BRIDGE_COMMAND", configured_payload["items"][0]["detected_env"])

    def test_provider_status_uses_env_file_without_leaking_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / "topdesk.env"
            env_file.write_text(
                "\n".join(
                    [
                        "TOPDESK_BASE_URL=https://topdesk.example.com",
                        "TOPDESK_USERNAME=agent",
                        "TOPDESK_PASSWORD=leak-check-topdesk",
                    ]
                ),
                encoding="utf-8",
            )
            result = self.run_cli(
                "provider",
                "status",
                "topdesk",
                "--env-file",
                str(env_file),
                "--json",
                env={"PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "provider-status")
        self.assertEqual(payload["status"], "ok")
        item = payload["items"][0]
        self.assertEqual(item["status"], "ok")
        self.assertIn("TOPDESK_BASE_URL", item["detected_env_file"])
        self.assertIn("TOPDESK_PASSWORD", item["detected_env_file"])
        self.assertTrue(item["credential_resolution"]["secret_values_returned"] is False)
        self.assertNotIn("leak-check-topdesk", result.stdout)
        self.assertNotIn("https://topdesk.example.com", result.stdout)

    def test_credential_resolve_json_env_file_without_leaking_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / "elastic.json"
            env_file.write_text(
                json.dumps(
                    {
                        "ELASTICSEARCH_URL": "https://elastic.example.com",
                        "ELASTICSEARCH_API_KEY": "leak-check-elastic",
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_cli(
                "credential",
                "resolve",
                "elasticsearch",
                "--env-file",
                str(env_file),
                "--json",
                env={"PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "credential-resolution")
        self.assertEqual(payload["provider"], "elasticsearch")
        self.assertEqual(payload["status"], "ok")
        self.assertIn("ELASTICSEARCH_URL", payload["detected_env_file"])
        self.assertIn("ELASTICSEARCH_API_KEY", payload["detected_env_file"])
        self.assertFalse(payload["secret_values_returned"])
        self.assertNotIn("leak-check-elastic", result.stdout)
        self.assertNotIn("https://elastic.example.com", result.stdout)

    def test_credential_resolver_prefers_env_over_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / "topdesk.env"
            env_file.write_text(
                "\n".join(
                    [
                        "TOPDESK_BASE_URL=https://file.example.com",
                        "TOPDESK_USERNAME=file-user",
                        "TOPDESK_PASSWORD=file-secret",
                    ]
                ),
                encoding="utf-8",
            )
            result = self.run_cli(
                "credential",
                "resolve",
                "topdesk",
                "--env-file",
                str(env_file),
                "--json",
                env={
                    "PATH": os.environ.get("PATH", ""),
                    "TOPDESK_BASE_URL": "https://env.example.com",
                    "TOPDESK_USERNAME": "env-user",
                    "TOPDESK_PASSWORD": "env-secret",
                },
                replace_env=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertIn("TOPDESK_BASE_URL", payload["detected_env"])
        self.assertIn("TOPDESK_PASSWORD", payload["detected_env"])
        self.assertNotIn("TOPDESK_BASE_URL", payload["detected_env_file"])
        self.assertNotIn("TOPDESK_PASSWORD", payload["detected_env_file"])
        self.assertNotIn("env-secret", result.stdout)
        self.assertNotIn("file-secret", result.stdout)

    def test_credential_resolver_respects_empty_env_mapping(self) -> None:
        provider = {
            "id": "sample",
            "auth_methods": [
                {
                    "id": "token",
                    "secret_fields": ["SAMPLE_TOKEN"],
                }
            ],
            "config_fields": [
                {
                    "name": "SAMPLE_URL",
                    "required": True,
                    "secret": False,
                }
            ],
        }

        result = resolve_provider_credentials(
            provider,
            env={},
            explicit={},
        )

        self.assertEqual(result["status"], "missing")
        self.assertIn("SAMPLE_URL", result["required_missing"])
        self.assertIn("SAMPLE_TOKEN", result["auth"]["missing_secret_fields"])

    def test_credential_backends_json(self) -> None:
        result = self.run_cli("credential", "backends", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "credential-backends")
        self.assertIn("env", payload["items"])
        self.assertIn("env-file", payload["items"])
        self.assertIn("os-keychain", payload["items"])
        self.assertIn("plain-session-only", payload["items"])
        details = {item["id"]: item for item in payload["details"]}
        self.assertIn(details["os-keychain"]["status"], {"available", "unavailable"})
        self.assertFalse(any(item["stores_secret"] for item in payload["details"]))
        self.assertFalse(payload["stored_secret"])

    def test_credential_resolve_missing_env_file_reports_safe_error(self) -> None:
        result = self.run_cli(
            "credential",
            "resolve",
            "topdesk",
            "--env-file",
            "/tmp/aikit-missing-secret-file.env",
            "--json",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("credential file not found", result.stderr)

    def test_provider_configure_needs_input_without_source(self) -> None:
        result = self.run_cli("provider", "configure", "elasticsearch", "--json")

        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "provider-configure")
        self.assertEqual(payload["status"], "needs-input")
        self.assertFalse(payload["stored_secret"])
        self.assertEqual(payload["provider"], "elasticsearch")

    def test_provider_configure_env_file_persists_refs_not_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as config_home:
            env_file = Path(tmpdir) / "topdesk.env"
            env_file.write_text(
                "\n".join(
                    [
                        "TOPDESK_BASE_URL=https://topdesk.example.com",
                        "TOPDESK_USERNAME=agent",
                        "TOPDESK_PASSWORD=leak-check-topdesk",
                    ]
                ),
                encoding="utf-8",
            )
            env = {"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")}
            configure = self.run_cli(
                "provider",
                "configure",
                "topdesk",
                "--env-file",
                str(env_file),
                "--json",
                env=env,
                replace_env=True,
            )
            status = self.run_cli(
                "provider",
                "status",
                "topdesk",
                "--json",
                env=env,
                replace_env=True,
            )
            config_text = (Path(config_home) / "config.json").read_text(encoding="utf-8")

        self.assertEqual(configure.returncode, 0, configure.stderr)
        configure_payload = json.loads(configure.stdout)
        self.assertEqual(configure_payload["kind"], "provider-configure")
        self.assertEqual(configure_payload["status"], "configured")
        self.assertFalse(configure_payload["stored_secret"])
        self.assertEqual(configure_payload["provider_status"], "ok")
        self.assertIn("env-file:", config_text)
        self.assertNotIn("leak-check-topdesk", configure.stdout)
        self.assertNotIn("leak-check-topdesk", config_text)
        self.assertNotIn("https://topdesk.example.com", configure.stdout)
        self.assertNotIn("https://topdesk.example.com", config_text)

        self.assertEqual(status.returncode, 0, status.stderr)
        status_payload = json.loads(status.stdout)
        self.assertEqual(status_payload["status"], "ok")
        self.assertIn("TOPDESK_PASSWORD", status_payload["items"][0]["detected_env_file"])
        self.assertNotIn("leak-check-topdesk", status.stdout)

    def test_provider_configure_env_refs_persists_refs_not_values(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            env = {
                "AIKIT_CONFIG_HOME": config_home,
                "PATH": os.environ.get("PATH", ""),
                "AZURE_DEVOPS_ORG": "example-org",
                "AZURE_DEVOPS_PAT": "leak-check-azure",
            }
            configure = self.run_cli(
                "provider",
                "configure",
                "azure-devops",
                "--env",
                "AZURE_DEVOPS_ORG",
                "--env",
                "AZURE_DEVOPS_PAT",
                "--json",
                env=env,
                replace_env=True,
            )
            status = self.run_cli(
                "provider",
                "status",
                "azure-devops",
                "--json",
                env=env,
                replace_env=True,
            )
            config_text = (Path(config_home) / "config.json").read_text(encoding="utf-8")

        self.assertEqual(configure.returncode, 0, configure.stderr)
        self.assertIn("env:AZURE_DEVOPS_PAT", config_text)
        self.assertNotIn("leak-check-azure", configure.stdout)
        self.assertNotIn("leak-check-azure", config_text)
        self.assertEqual(json.loads(status.stdout)["status"], "ok")

    def test_provider_configure_from_env_persists_refs_not_values(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            env = {
                "AIKIT_CONFIG_HOME": config_home,
                "PATH": os.environ.get("PATH", ""),
                "AZURE_DEVOPS_ORG": "example-org",
                "AZURE_DEVOPS_PAT": "leak-check-from-env",
            }
            result = self.run_cli(
                "provider",
                "configure",
                "azure-devops",
                "--from-env",
                "--json",
                env=env,
                replace_env=True,
            )
            config_text = (Path(config_home) / "config.json").read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "configured")
        self.assertEqual(payload["provider_status"], "ok")
        self.assertIn("env:AZURE_DEVOPS_ORG", config_text)
        self.assertIn("env:AZURE_DEVOPS_PAT", config_text)
        self.assertNotIn("leak-check-from-env", result.stdout)
        self.assertNotIn("leak-check-from-env", config_text)

    def test_provider_configure_env_file_without_provider_fields_does_not_write_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as config_home:
            env_file = Path(tmpdir) / "wrong.env"
            env_file.write_text("UNRELATED_SECRET=leak-check-unused\n", encoding="utf-8")
            result = self.run_cli(
                "provider",
                "configure",
                "topdesk",
                "--env-file",
                str(env_file),
                "--json",
                env={"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "needs-input")
        self.assertIn(str(env_file.resolve()), payload["env_files_without_provider_fields"])
        self.assertFalse((Path(config_home) / "config.json").exists())
        self.assertNotIn("leak-check-unused", result.stdout)

    def test_provider_configure_session_only_does_not_write_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as config_home:
            env_file = Path(tmpdir) / "topdesk.env"
            env_file.write_text(
                "TOPDESK_BASE_URL=https://topdesk.example.com\nTOPDESK_USERNAME=agent\nTOPDESK_PASSWORD=leak-check-session\n",
                encoding="utf-8",
            )
            result = self.run_cli(
                "provider",
                "configure",
                "topdesk",
                "--env-file",
                str(env_file),
                "--session-only",
                "--json",
                env={"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "session-only")
        self.assertTrue(payload["session_only"])
        self.assertFalse((Path(config_home) / "config.json").exists())
        self.assertNotIn("leak-check-session", result.stdout)

    def test_provider_unset_removes_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as config_home:
            env_file = Path(tmpdir) / "topdesk.env"
            env_file.write_text(
                "TOPDESK_BASE_URL=https://topdesk.example.com\nTOPDESK_USERNAME=agent\nTOPDESK_PASSWORD=leak-check-unset\n",
                encoding="utf-8",
            )
            env = {"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")}
            configure = self.run_cli(
                "provider",
                "configure",
                "topdesk",
                "--env-file",
                str(env_file),
                "--json",
                env=env,
                replace_env=True,
            )
            unset = self.run_cli("provider", "unset", "topdesk", "--json", env=env, replace_env=True)
            config_text = (Path(config_home) / "config.json").read_text(encoding="utf-8")

        self.assertEqual(configure.returncode, 0, configure.stderr)
        self.assertEqual(unset.returncode, 0, unset.stderr)
        self.assertEqual(json.loads(unset.stdout)["status"], "removed")
        self.assertNotIn("topdesk", config_text)

    def test_provider_configure_rejects_raw_env_value(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_cli(
                "provider",
                "configure",
                "topdesk",
                "--env",
                "TOPDESK_PASSWORD=secret",
                "--json",
                env={"AIKIT_CONFIG_HOME": config_home},
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--env must be an environment variable name", result.stderr)
        self.assertFalse((Path(config_home) / "config.json").exists())

    def test_llm_list_json(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_cli("llm", "list", "--json", env={"AIKIT_CONFIG_HOME": config_home})

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "llm-backends")
        backends = {item["id"] for item in payload["items"]}
        self.assertIn("openai", backends)
        self.assertIn("anthropic", backends)
        self.assertIn("openrouter", backends)
        self.assertIn("ollama", backends)
        self.assertIn("codex-cli", backends)
        self.assertIn("claude-code", backends)

    def test_llm_configure_openai_stores_env_ref_not_secret(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            env = {
                "AIKIT_CONFIG_HOME": config_home,
                "TEST_OPENAI_API_KEY": "secret-value-that-must-not-leak",
            }
            configure = self.run_cli(
                "llm",
                "configure",
                "openai",
                "--api-key-env",
                "TEST_OPENAI_API_KEY",
                "--base-url",
                "https://example.test/v1",
                "--model",
                "gpt-test",
                "--set-default",
                "--json",
                env=env,
            )
            doctor = self.run_cli("llm", "doctor", "openai", "--json", env=env)
            config_text = (Path(config_home) / "config.json").read_text(encoding="utf-8")

        self.assertEqual(configure.returncode, 0, configure.stderr)
        configure_payload = json.loads(configure.stdout)
        self.assertEqual(configure_payload["kind"], "llm-configure")
        self.assertFalse(configure_payload["stored_secret"])
        self.assertEqual(configure_payload["default"], "openai")
        self.assertNotIn("secret-value-that-must-not-leak", configure.stdout)
        self.assertNotIn("secret-value-that-must-not-leak", config_text)
        self.assertIn("env:TEST_OPENAI_API_KEY", config_text)

        self.assertEqual(doctor.returncode, 0, doctor.stderr)
        doctor_payload = json.loads(doctor.stdout)
        self.assertEqual(doctor_payload["kind"], "llm-doctor")
        self.assertEqual(doctor_payload["status"], "ok")
        self.assertTrue(doctor_payload["items"][0]["api_key_present"])
        self.assertNotIn("secret-value-that-must-not-leak", doctor.stdout)

    def test_llm_configure_rejects_raw_secret_as_api_key_env(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_cli(
                "llm",
                "configure",
                "openai",
                "--api-key-env",
                "sk-test-secret-value",
                "--json",
                env={"AIKIT_CONFIG_HOME": config_home},
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--api-key-env must be an environment variable name", result.stderr)
        self.assertFalse((Path(config_home) / "config.json").exists())

    def test_llm_doctor_missing_openai_reports_missing_without_failure(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_cli("llm", "doctor", "openai", "--json", env={"AIKIT_CONFIG_HOME": config_home})

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "llm-doctor")
        self.assertEqual(payload["status"], "missing")
        self.assertFalse(payload["items"][0]["api_key_present"])

    def test_llm_doctor_codex_cli_does_not_require_installation(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_cli("llm", "doctor", "codex-cli", "--json", env={"AIKIT_CONFIG_HOME": config_home})

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "llm-doctor")
        self.assertEqual(payload["items"][0]["id"], "codex-cli")
        self.assertIn(payload["items"][0]["status"], {"ok", "missing"})
        self.assertEqual(payload["items"][0]["auth_status"], "external")

    def test_agent_with_configured_backend_resolves_llm_without_prompt_leak(self) -> None:
        server, base_url = self.fake_llm_server()
        try:
            config_home = tempfile.TemporaryDirectory()
            self.addCleanup(config_home.cleanup)
            env = {
                "AIKIT_CONFIG_HOME": config_home.name,
                "TEST_OPENAI_API_KEY": "secret-value-that-must-not-leak",
            }
            configure = self.run_cli(
                "llm",
                "configure",
                "openai",
                "--api-key-env",
                "TEST_OPENAI_API_KEY",
                "--base-url",
                base_url,
                "--model",
                "fake-model",
                "--set-default",
                "--json",
                env=env,
            )
            result = self.run_cli("agent", "--json", "senha=abc123", "analise esse incidente", env=env)
        finally:
            server.shutdown()
            server.server_close()

        self.assertEqual(configure.returncode, 0, configure.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "agent")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["llm_backend"], "openai")
        self.assertEqual(payload["llm_backend_status"], "ok")
        self.assertIn("agent run", payload["response"])
        self.assertNotIn("prompt", payload)
        self.assertNotIn("senha=abc123", result.stdout)
        self.assertNotIn("secret-value-that-must-not-leak", result.stdout)

    def test_agent_entrypoint_defaults_to_natural_language_prompt(self) -> None:
        server, base_url = self.fake_llm_server()
        try:
            config_home = tempfile.TemporaryDirectory()
            self.addCleanup(config_home.cleanup)
            env = {
                "AIKIT_CONFIG_HOME": config_home.name,
                "TEST_OPENAI_API_KEY": "secret-value-that-must-not-leak",
            }
            configure = self.run_cli(
                "llm",
                "configure",
                "openai",
                "--api-key-env",
                "TEST_OPENAI_API_KEY",
                "--base-url",
                base_url,
                "--model",
                "fake-model",
                "--set-default",
                "--json",
                env=env,
            )
            result = self.run_agent("--json", "analise esse incidente", env=env)
        finally:
            server.shutdown()
            server.server_close()

        self.assertEqual(configure.returncode, 0, configure.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "agent")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["llm_backend"], "openai")
        self.assertIn("agent run", payload["response"])

    def test_source_add_list_status_and_remove_without_secret_leak(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            env = {
                "AIKIT_CONFIG_HOME": config_home,
                "PATH": os.environ.get("PATH", ""),
                "AZURE_DEVOPS_PAT": "secret-source-value",
            }
            configure = self.run_cli(
                "source",
                "add",
                "azure-sustentacao",
                "--provider",
                "azure-devops",
                "--label",
                "Azure Sustentacao",
                "--config",
                "project=Sustentacao",
                "--env",
                "AZURE_DEVOPS_PAT=AZURE_DEVOPS_PAT",
                "--default-for",
                "card",
                "--default-for-agent",
                "azure-devops-orchestrator",
                "--set-default",
                "--json",
                env=env,
                replace_env=True,
            )
            listing = self.run_cli("source", "list", "--json", env=env, replace_env=True)
            status = self.run_cli("source", "status", "azure-sustentacao", "--json", env=env, replace_env=True)
            remove = self.run_cli("source", "remove", "azure-sustentacao", "--json", env=env, replace_env=True)
            config_text = (Path(config_home) / "config.json").read_text(encoding="utf-8")

        self.assertEqual(configure.returncode, 0, configure.stderr)
        configure_payload = json.loads(configure.stdout)
        self.assertEqual(configure_payload["kind"], "source-configure")
        self.assertFalse(configure_payload["stored_secret"])
        self.assertEqual(configure_payload["source"]["id"], "azure-sustentacao")
        self.assertEqual(configure_payload["defaults"]["intents"]["card"], "azure-sustentacao")
        self.assertEqual(listing.returncode, 0, listing.stderr)
        self.assertEqual(json.loads(listing.stdout)["items"][0]["id"], "azure-sustentacao")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(json.loads(status.stdout)["items"][0]["status"], "ok")
        self.assertEqual(remove.returncode, 0, remove.stderr)
        self.assertNotIn("secret-source-value", configure.stdout)
        self.assertNotIn("secret-source-value", listing.stdout)
        self.assertNotIn("secret-source-value", status.stdout)
        self.assertNotIn("secret-source-value", config_text)

    def test_source_add_rejects_secret_config_without_persisting(self) -> None:
        unsafe_configs = [
            "conn_string=postgresql://user:pass@localhost/db",
            "database_url=postgresql://user:pass@localhost/db",
            "password=plain-password",
            "api_key=sk-1234567890abcdef",
            "url=https://user:pass@example.com",
        ]

        for config_pair in unsafe_configs:
            with self.subTest(config_pair=config_pair), tempfile.TemporaryDirectory() as config_home:
                env = {"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")}
                result = self.run_cli(
                    "source",
                    "add",
                    "unsafe-source",
                    "--provider",
                    "postgres",
                    "--config",
                    config_pair,
                    "--json",
                    env=env,
                    replace_env=True,
                )

                self.assertEqual(result.returncode, 2)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["kind"], "source-configure")
                self.assertEqual(payload["status"], "blocked")
                self.assertFalse(payload["ok"])
                self.assertIn(payload["reason"], {"secret-like-config-value", "provider-secret-field"})
                self.assertFalse(payload["stored_secret"])
                self.assertIn("use --env", payload["message"])
                self.assertNotIn(config_pair.split("=", 1)[1], result.stdout)
                self.assertEqual(result.stderr, "")
                self.assertFalse((Path(config_home) / "config.json").exists())

    def test_source_add_rejects_provider_secret_config_metadata_without_persisting(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            env = {"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")}
            result = self.run_cli(
                "source",
                "add",
                "bpo-source",
                "--provider",
                "bpo",
                "--config",
                "BPO_FORBIDDEN_URL_PATTERNS=internal.example",
                "--json",
                env=env,
                replace_env=True,
            )

        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["reason"], "provider-secret-field")
        self.assertEqual(payload["field"], "BPO_FORBIDDEN_URL_PATTERNS")
        self.assertEqual(payload["provider"], "bpo")
        self.assertFalse(payload["stored_secret"])
        self.assertNotIn("internal.example", result.stdout)
        self.assertFalse((Path(config_home) / "config.json").exists())

    def test_source_add_accepts_env_ref_for_connection_string(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            env = {
                "AIKIT_CONFIG_HOME": config_home,
                "PATH": os.environ.get("PATH", ""),
                "LOCAL_POSTGRES_URL": "postgresql://user:pass@localhost/db",
            }
            result = self.run_cli(
                "source",
                "add",
                "postgres-local",
                "--provider",
                "postgres",
                "--env",
                "POSTGRES_DB_CONN_STRING=LOCAL_POSTGRES_URL",
                "--json",
                env=env,
                replace_env=True,
            )
            config_text = (Path(config_home) / "config.json").read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["stored_secret"])
        self.assertEqual(payload["source"]["env_refs"]["POSTGRES_DB_CONN_STRING"], "LOCAL_POSTGRES_URL")
        self.assertNotIn("postgresql://user:pass@localhost/db", result.stdout)
        self.assertNotIn("postgresql://user:pass@localhost/db", config_text)

    def test_source_add_allows_safe_path_and_pattern_config_keys(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            env = {"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")}
            result = self.run_cli(
                "source",
                "add",
                "safe-source",
                "--provider",
                "elasticsearch",
                "--config",
                "path=/tmp/logs.json",
                "--config",
                "pattern=error-*",
                "--json",
                env=env,
                replace_env=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["stored_secret"])
        self.assertEqual(payload["source"]["config"]["path"], "/tmp/logs.json")
        self.assertEqual(payload["source"]["config"]["pattern"], "error-*")

    def test_source_env_uses_declarative_contract_and_ignores_unsafe_config_values(self) -> None:
        env = source_env(
            {
                "provider": "elasticsearch",
                "config": {
                    "url": "https://user:pass@example.com",
                    "default_time_field": "@timestamp",
                },
                "env_refs": {},
            },
            {
                "env": {
                    "url": "ELASTICSEARCH_URL",
                    "default_time_field": "ELASTICSEARCH_DEFAULT_TIME_FIELD",
                },
            },
        )

        self.assertNotIn("ELASTICSEARCH_URL", env)
        self.assertEqual(env["ELASTICSEARCH_DEFAULT_TIME_FIELD"], "@timestamp")

    def test_source_list_and_status_redact_legacy_secret_config(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            config_path = Path(config_home) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "llm": {"default": None, "backends": {}},
                        "sources": {
                            "items": {
                                "legacy-postgres": {
                                    "id": "legacy-postgres",
                                    "provider": "postgres",
                                    "label": "Legacy Postgres",
                                    "config": {
                                        "conn_string": "postgresql://user:pass@localhost/db",
                                        "project": "analytics",
                                    },
                                    "env_refs": {},
                                    "env_files": [],
                                    "defaults": {"intents": [], "agents": []},
                                }
                            },
                            "defaults": {"providers": {}, "intents": {}, "agents": {}},
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            env = {"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")}
            listing = self.run_cli("source", "list", "--json", env=env, replace_env=True)
            status = self.run_cli("source", "status", "legacy-postgres", "--json", env=env, replace_env=True)

        self.assertEqual(listing.returncode, 0, listing.stderr)
        self.assertEqual(status.returncode, 0, status.stderr)
        listing_payload = json.loads(listing.stdout)
        status_payload = json.loads(status.stdout)
        item = listing_payload["items"][0]
        status_item = status_payload["items"][0]
        self.assertTrue(listing_payload["stored_secret"])
        self.assertTrue(item["stored_secret"])
        self.assertEqual(item["config"]["conn_string"], "[REDACTED_SECRET]")
        self.assertEqual(item["config"]["project"], "analytics")
        self.assertEqual(item["unsafe_config_keys"], ["conn_string"])
        self.assertEqual(status_payload["status"], "partial")
        self.assertEqual(status_item["status"], "unsafe")
        self.assertTrue(status_item["next_steps"])
        self.assertNotIn("postgresql://user:pass@localhost/db", listing.stdout)
        self.assertNotIn("postgresql://user:pass@localhost/db", status.stdout)

    def test_source_blocked_attempt_is_audited_without_raw_value(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            raw_value = "internal.example"
            env = {"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")}
            blocked = self.run_cli(
                "source",
                "add",
                "bpo-source",
                "--provider",
                "bpo",
                "--config",
                f"BPO_FORBIDDEN_URL_PATTERNS={raw_value}",
                "--json",
                env=env,
                replace_env=True,
            )
            payload = json.loads(blocked.stdout)
            show = self.run_cli("audit", "show", payload["audit"]["id"], "--json", env=env, replace_env=True)

        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(show.returncode, 0, show.stderr)
        audit_payload = json.loads(show.stdout)
        sources = audit_payload["entry"]["sources"]
        self.assertEqual(sources[0]["id"], "bpo-source")
        self.assertEqual(sources[0]["field"], "BPO_FORBIDDEN_URL_PATTERNS")
        self.assertEqual(sources[0]["reason"], "provider-secret-field")
        self.assertNotIn(raw_value, show.stdout)

    def test_agent_prompt_card_requires_source_when_none_configured(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_agent(
                "--json",
                "analise o problema relatado no card 9900",
                env={"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "agent")
        self.assertEqual(payload["status"], "needs-input")
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["requires_source"])
        self.assertEqual(payload["source_provider"], "azure-devops")
        self.assertEqual(payload["provider"], "azure-devops")
        self.assertEqual(payload["route"]["agent_id"], "azure-devops-orchestrator")
        self.assertNotIn("requires_llm", payload)
        self.assertEqual(payload["setup_wizard"]["kind"], "provider-setup-wizard")
        self.assertEqual(payload["setup_wizard"]["next_question"]["id"], "azure_devops_opt_in")
        self.assertFalse(any("agent source add" in step for step in payload["next_steps"]))

    def test_agent_prompt_card_uses_default_source_and_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as config_home, tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.write_card_fixture(Path(tmpdir) / "card-9900.json", card_id=9900)
            fake_codex = self.write_fake_host_cli(tmpdir, "codex", "REVIEW OK")
            env = {"AIKIT_CONFIG_HOME": config_home, "PATH": f"{tmpdir}:{os.environ.get('PATH', '')}"}
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
                replace_env=True,
            )
            reviewer = self.run_agent(
                "llm",
                "configure",
                "codex-cli",
                "--command",
                str(fake_codex),
                "--json",
                env=env,
                replace_env=True,
            )
            result = self.run_agent(
                "--json",
                "analise o problema relatado no card 9900",
                env=env,
                replace_env=True,
            )
            memory = self.run_agent("memory", "show", "--json", env=env, replace_env=True)
            reset = self.run_agent("memory", "reset", "--json", env=env, replace_env=True)
            after_reset = self.run_agent("memory", "show", "--json", env=env, replace_env=True)

        self.assertEqual(configure.returncode, 0, configure.stderr)
        self.assertEqual(reviewer.returncode, 0, reviewer.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "agent")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["mode"], "agentic-route")
        self.assertEqual(payload["legacy_mode"], "deterministic-route")
        self.assertEqual(payload["source"]["id"], "azure-fixture")
        self.assertEqual(payload["route"]["entities"]["card_id"], "9900")
        self.assertIn("# Card Analysis", payload["response"])
        self.assertIn("- ID: 9900", payload["response"])
        self.assertEqual(payload["review_result"]["status"], "ok")
        self.assertEqual(payload["review_gate"]["status"], "reviewed")
        self.assertEqual(memory.returncode, 0, memory.stderr)
        memory_payload = json.loads(memory.stdout)
        self.assertEqual(memory_payload["kind"], "memory")
        self.assertTrue(memory_payload["usage"]["prompts"])
        self.assertTrue(memory_payload["usage"]["sources"])
        self.assertEqual(reset.returncode, 0, reset.stderr)
        self.assertEqual(json.loads(reset.stdout)["status"], "reset")
        self.assertEqual(after_reset.returncode, 0, after_reset.stderr)
        self.assertEqual(json.loads(after_reset.stdout)["usage"]["prompts"], [])

    def test_run_with_source_injects_fixture_for_read_card(self) -> None:
        with tempfile.TemporaryDirectory() as config_home, tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.write_card_fixture(Path(tmpdir) / "card-9901.json", card_id=9901)
            env = {"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")}
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
                "--json",
                env=env,
                replace_env=True,
            )
            result = self.run_agent(
                "--json",
                "run",
                "azure-devops-orchestrator",
                "read-card",
                "--id",
                "9901",
                "--source",
                "azure-fixture",
                env=env,
                replace_env=True,
            )

        self.assertEqual(configure.returncode, 0, configure.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "run")
        self.assertEqual(payload["status"], "ok")
        self.assertIn("# Card Analysis", payload["stdout"])
        self.assertIn("- ID: 9901", payload["stdout"])

    def test_agent_with_anthropic_backend_uses_configured_base_url(self) -> None:
        server, base_url = self.fake_anthropic_server()
        try:
            config_home = tempfile.TemporaryDirectory()
            self.addCleanup(config_home.cleanup)
            env = {
                "AIKIT_CONFIG_HOME": config_home.name,
                "TEST_ANTHROPIC_API_KEY": "secret-anthropic-value",
            }
            configure = self.run_cli(
                "llm",
                "configure",
                "anthropic",
                "--api-key-env",
                "TEST_ANTHROPIC_API_KEY",
                "--base-url",
                base_url,
                "--model",
                "fake-claude",
                "--set-default",
                "--json",
                env=env,
            )
            result = self.run_cli("agent", "--json", "analise esse incidente", env=env)
        finally:
            server.shutdown()
            server.server_close()

        self.assertEqual(configure.returncode, 0, configure.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "agent")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["llm_backend"], "anthropic")
        self.assertIn("Anthropic fake", payload["response"])
        self.assertNotIn("secret-anthropic-value", result.stdout)

    def test_agent_with_openrouter_backend_uses_openai_compatible_flow(self) -> None:
        server, base_url = self.fake_llm_server()
        try:
            config_home = tempfile.TemporaryDirectory()
            self.addCleanup(config_home.cleanup)
            env = {
                "AIKIT_CONFIG_HOME": config_home.name,
                "TEST_OPENROUTER_API_KEY": "secret-openrouter-value",
            }
            configure = self.run_cli(
                "llm",
                "configure",
                "openrouter",
                "--api-key-env",
                "TEST_OPENROUTER_API_KEY",
                "--base-url",
                base_url,
                "--model",
                "fake/openrouter",
                "--set-default",
                "--json",
                env=env,
            )
            result = self.run_cli("agent", "--json", "analise esse incidente", env=env)
        finally:
            server.shutdown()
            server.server_close()

        self.assertEqual(configure.returncode, 0, configure.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["llm_backend"], "openrouter")
        self.assertIn("agent run", payload["response"])
        self.assertNotIn("secret-openrouter-value", result.stdout)

    def test_agent_with_ollama_backend_uses_openai_compatible_flow_without_key(self) -> None:
        server, base_url = self.fake_llm_server()
        try:
            config_home = tempfile.TemporaryDirectory()
            self.addCleanup(config_home.cleanup)
            env = {"AIKIT_CONFIG_HOME": config_home.name}
            configure = self.run_cli(
                "llm",
                "configure",
                "ollama",
                "--base-url",
                base_url,
                "--model",
                "fake-ollama",
                "--set-default",
                "--json",
                env=env,
            )
            result = self.run_cli("agent", "--json", "analise esse incidente", env=env)
        finally:
            server.shutdown()
            server.server_close()

        self.assertEqual(configure.returncode, 0, configure.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["llm_backend"], "ollama")
        self.assertIn("agent run", payload["response"])

    def test_agent_with_codex_cli_backend_uses_configured_host_command(self) -> None:
        with tempfile.TemporaryDirectory() as config_home, tempfile.TemporaryDirectory() as bin_dir:
            fake_codex = self.write_fake_host_cli(bin_dir, "codex", "fake codex response")
            env = {"AIKIT_CONFIG_HOME": config_home, "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"}
            configure = self.run_cli(
                "llm",
                "configure",
                "codex-cli",
                "--command",
                str(fake_codex),
                "--set-default",
                "--json",
                env=env,
                replace_env=True,
            )
            result = self.run_cli("agent", "--json", "analise esse incidente", env=env, replace_env=True)

        self.assertEqual(configure.returncode, 0, configure.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["llm_backend"], "codex-cli")
        self.assertEqual(payload["response"], "fake codex response")

    def test_agent_with_claude_code_backend_uses_configured_host_command(self) -> None:
        with tempfile.TemporaryDirectory() as config_home, tempfile.TemporaryDirectory() as bin_dir:
            fake_claude = self.write_fake_host_cli(bin_dir, "claude", "fake claude response")
            env = {"AIKIT_CONFIG_HOME": config_home, "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"}
            configure = self.run_cli(
                "llm",
                "configure",
                "claude-code",
                "--command",
                str(fake_claude),
                "--set-default",
                "--json",
                env=env,
                replace_env=True,
            )
            result = self.run_cli("agent", "--json", "analise esse incidente", env=env, replace_env=True)

        self.assertEqual(configure.returncode, 0, configure.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["llm_backend"], "claude-code")
        self.assertEqual(payload["response"], "fake claude response")

    def test_agent_requires_llm_backend(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_cli(
                "agent",
                "--json",
                "senha=abc123",
                "analise esse incidente",
                env={"AIKIT_CONFIG_HOME": config_home},
            )

        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "agent")
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["requires_llm"])
        self.assertTrue(payload["prompt_received"])
        self.assertNotIn("prompt", payload)
        self.assertNotIn("senha=abc123", result.stdout)
        self.assertIn("requires a configured LLM backend", payload["message"])
        self.assertIn("agent run <agent> <capability>", payload["next_steps"][0])

    def test_agent_requires_prompt(self) -> None:
        result = self.run_cli("agent")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("agent requires a natural-language prompt", result.stderr)

    def test_run_applies_provider_fallback_when_required_provider_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_cli(
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
                env={"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "run")
        self.assertEqual(payload["status"], "partial")
        self.assertEqual(payload["schema_version"], "ai-devkit.run/v1")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["agent_id"], "elasticsearch-log-analyzer")
        self.assertEqual(payload["capability_id"], "search-log-events")
        self.assertEqual(payload["agent"]["id"], "elasticsearch-log-analyzer")
        self.assertEqual(payload["capability"], "elasticsearch-log-analyzer.search-log-events")
        self.assertEqual(payload["providers"]["missing"], ["elasticsearch"])
        self.assertEqual(payload["providers"]["skipped"], ["elasticsearch"])
        self.assertEqual(payload["fallback_applied"], "plan_only")
        self.assertEqual(payload["stdout"], "")
        self.assertIn("Logs reais nao foram consultados.", payload["risks"])
        self.assertEqual(payload["setup_wizard"]["provider"], "elasticsearch")
        self.assertEqual(payload["setup_wizard"]["owner_agent"], "provider-configurator")
        self.assertEqual(payload["next_question"]["id"], "elasticsearch_opt_in")
        self.assertFalse(any("agent provider configure elasticsearch" in step for step in payload["next_steps"]))

    def test_run_executes_when_required_provider_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as config_home, tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "events.json"
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
                                "trace_id": "trace-1",
                                "message": "payment failed",
                                "id": "evt-1",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_cli(
                "--json",
                "run",
                "elasticsearch-log-analyzer",
                "search-log-events",
                "--fixture",
                str(fixture),
                env={
                    "AIKIT_CONFIG_HOME": config_home,
                    "PATH": os.environ.get("PATH", ""),
                    "ELASTICSEARCH_URL": "https://elastic.example.com",
                    "ELASTICSEARCH_API_KEY": "leak-check-elastic-runtime",
                },
                replace_env=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "run")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["schema_version"], "ai-devkit.run/v1")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["agent_id"], "elasticsearch-log-analyzer")
        self.assertEqual(payload["capability_id"], "search-log-events")
        self.assertEqual(payload["providers"]["used"], ["elasticsearch"])
        self.assertEqual(payload["providers"]["missing"], [])
        self.assertEqual(payload["fallback_applied"], None)
        self.assertIn("# Elasticsearch Log Events", payload["stdout"])
        self.assertIn("payment failed", payload["stdout"])
        self.assertNotIn("leak-check-elastic-runtime", result.stdout)

    def test_fallback_evaluator_treats_unknown_provider_as_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "providers").mkdir()
            result = evaluate_provider_requirements(
                root,
                {
                    "requires": {
                        "providers": [
                            {
                                "id": "missing-provider",
                                "mode": "required",
                                "fallback": "manual_steps",
                            }
                        ]
                    }
                },
            )

        self.assertFalse(result["ready"])
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["providers"]["missing"], ["missing-provider"])
        self.assertEqual(result["providers"]["skipped"], ["missing-provider"])
        self.assertEqual(result["fallback_applied"], "manual_steps")

    def test_run_falls_back_when_configured_provider_env_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            missing_env_file = Path(config_home) / "deleted.env"
            config_path = Path(config_home) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "providers": {
                            "elasticsearch": {
                                "provider": "elasticsearch",
                                "refs": {},
                                "env_files": [
                                    {
                                        "path": str(missing_env_file),
                                        "fields": [
                                            {
                                                "name": "ELASTICSEARCH_API_KEY",
                                                "ref": f"env-file:{missing_env_file}#ELASTICSEARCH_API_KEY",
                                                "secret": True,
                                            }
                                        ],
                                    }
                                ],
                                "stored_secret": False,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = self.run_cli(
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
                env={"AIKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "partial")
        self.assertEqual(payload["providers"]["missing"], ["elasticsearch"])
        self.assertEqual(payload["fallback_applied"], "plan_only")
        self.assertIn("Logs reais nao foram consultados.", payload["risks"])

    def test_run_blocks_mutating_execute_without_runtime_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "card.json"
            fixture.write_text(
                json.dumps({"work_item": {"id": 123, "title": "Bug", "state": "Active"}}),
                encoding="utf-8",
            )
            result = self.run_cli(
                "--json",
                "run",
                "azure-devops-orchestrator",
                "comment-card",
                "--fixture",
                str(fixture),
                "--comment",
                "Investigacao registrada",
                "--execute",
            )

        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "run")
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["schema_version"], "ai-devkit.run/v1")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["agent_id"], "azure-devops-orchestrator")
        self.assertEqual(payload["capability_id"], "comment-card")
        self.assertEqual(payload["guardrail"]["reason"], "missing_runtime_confirmation")
        self.assertIn("--confirm-execute", payload["next_steps"][0])
        self.assertEqual(payload["runner"], None)

    def test_execution_guardrail_blocks_runner_confirmation_flags_without_runtime_confirmation(self) -> None:
        cases = [
            ("--yes-confirm", "confirm"),
            ("--yes-save", "ask_before_write"),
            ("--yes-save", "local_write"),
            ("--yes-save", "local-config-write"),
        ]

        for flag, write_policy in cases:
            with self.subTest(flag=flag, write_policy=write_policy):
                blocked = evaluate_execution_guardrails({"write_policy": write_policy}, [flag])
                allowed = evaluate_execution_guardrails(
                    {"write_policy": write_policy},
                    [flag, "--confirm-execute"],
                )

                self.assertFalse(blocked["ready"])
                self.assertEqual(blocked["reason"], "missing_runtime_confirmation")
                self.assertTrue(allowed["ready"])
                self.assertIn(flag, allowed["args"])
                self.assertNotIn("--confirm-execute", allowed["args"])

    def test_execution_guardrail_blocks_unknown_write_policy(self) -> None:
        blocked = evaluate_execution_guardrails({"write_policy": "write_whenever"}, [])

        self.assertFalse(blocked["ready"])
        self.assertEqual(blocked["reason"], "unknown_write_policy")
        self.assertEqual(blocked["write_policy"], "write_whenever")

    def test_run_allows_mutating_dry_run_without_runtime_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "card.json"
            fixture.write_text(
                json.dumps({"work_item": {"id": 123, "title": "Bug", "state": "Active"}}),
                encoding="utf-8",
            )
            result = self.run_cli(
                "--json",
                "run",
                "azure-devops-orchestrator",
                "comment-card",
                "--fixture",
                str(fixture),
                "--comment",
                "Investigacao registrada",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertIn("- Status: planned", payload["stdout"])
        self.assertNotIn("guardrail", payload)

    def test_run_strips_runtime_confirmation_before_runner_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "card.json"
            fixture.write_text(
                json.dumps({"work_item": {"id": 123, "title": "Bug", "state": "Active"}}),
                encoding="utf-8",
            )
            result = self.run_cli(
                "--json",
                "run",
                "azure-devops-orchestrator",
                "comment-card",
                "--fixture",
                str(fixture),
                "--comment",
                "Investigacao registrada",
                "--execute",
                "--confirm-execute",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertIn("- Status: executed", payload["stdout"])
        self.assertNotIn("unrecognized arguments", payload["stderr"])

    def test_run_blocks_dangerous_capability_even_with_execute_until_explicitly_allowed(self) -> None:
        result = self.run_cli(
            "--json",
            "run",
            "aws-operations-operator",
            "purge-sqs-queue-plan",
            "--queue-url",
            "https://sqs.us-east-1.amazonaws.com/123/q",
            "--environment",
            "prod",
            "--execute",
            "--confirm-execute",
        )

        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["guardrail"]["reason"], "dangerous_by_default")
        self.assertIn("--allow-dangerous", payload["next_steps"][0])

    def test_run_json_returns_standard_failed_payload_for_runner_error(self) -> None:
        agent_id = "failed-output-agent"
        capability_id = "fail-runner"
        with tempfile.TemporaryDirectory() as tmpdir:
            test_root = Path(tmpdir)
            agent_dir = test_root / "agents" / agent_id
            capability_dir = agent_dir / "capabilities" / capability_id
            capability_dir.mkdir(parents=True)
            (agent_dir / "agent.yaml").write_text(
                f"id: {agent_id}\nkind: specialist-agent\nname: Failed Output Agent\nstatus: draft\n",
                encoding="utf-8",
            )
            (capability_dir / "capability.yaml").write_text(
                f"id: {agent_id}.{capability_id}\nkind: capability\nname: Fail Runner\nstatus: draft\nentrypoint:\n  runner: runner.py\n",
                encoding="utf-8",
            )
            (capability_dir / "runner.py").write_text(
                "import sys\nprint('stdout evidence')\nprint('stderr evidence', file=sys.stderr)\nraise SystemExit(7)\n",
                encoding="utf-8",
            )

            result = self.run_cli(
                "--json",
                "run",
                agent_id,
                capability_id,
                env={"AI_DEVKIT_ROOT": str(test_root), "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 7, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "run")
        self.assertEqual(payload["schema_version"], "ai-devkit.run/v1")
        self.assertEqual(payload["status"], "failed")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["agent_id"], agent_id)
        self.assertEqual(payload["capability_id"], capability_id)
        self.assertEqual(payload["returncode"], 7)
        self.assertEqual(payload["exit_code"], 7)
        self.assertIn("stdout evidence", payload["stdout"])
        self.assertIn("stderr evidence", payload["stderr"])
        self.assertIn("stderr evidence", payload["error"])
        self.assertEqual(payload["providers"]["used"], [])
        self.assertEqual(payload["providers"]["missing"], [])
        self.assertEqual(payload["providers"]["skipped"], [])
        self.assertIsNone(payload["fallback_applied"])
        self.assertIsInstance(payload["evidence"], list)
        self.assertIsInstance(payload["risks"], list)
        self.assertIsInstance(payload["next_steps"], list)
        self.assertIsInstance(payload["artifacts"], list)

    def test_run_json_returns_standard_failed_payload_for_missing_runner(self) -> None:
        agent_id = "missing-runner-agent"
        capability_id = "missing-runner"
        with tempfile.TemporaryDirectory() as tmpdir:
            test_root = Path(tmpdir)
            agent_dir = test_root / "agents" / agent_id
            capability_dir = agent_dir / "capabilities" / capability_id
            capability_dir.mkdir(parents=True)
            (agent_dir / "agent.yaml").write_text(
                f"id: {agent_id}\nkind: specialist-agent\nname: Missing Runner Agent\nstatus: draft\n",
                encoding="utf-8",
            )
            (capability_dir / "capability.yaml").write_text(
                f"id: {agent_id}.{capability_id}\nkind: capability\nname: Missing Runner\nstatus: draft\nentrypoint:\n  runner: missing.py\n",
                encoding="utf-8",
            )

            result = self.run_cli(
                "--json",
                "run",
                agent_id,
                capability_id,
                env={"AI_DEVKIT_ROOT": str(test_root), "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "run")
        self.assertEqual(payload["schema_version"], "ai-devkit.run/v1")
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["agent_id"], agent_id)
        self.assertEqual(payload["capability_id"], capability_id)
        self.assertEqual(payload["returncode"], 2)
        self.assertEqual(payload["exit_code"], 2)
        self.assertIn("runner not found", payload["error"])

    def test_run_json_returns_standard_failed_payload_for_runner_timeout(self) -> None:
        agent_id = "timeout-output-agent"
        capability_id = "sleep-runner"
        with tempfile.TemporaryDirectory() as tmpdir:
            test_root = Path(tmpdir)
            agent_dir = test_root / "agents" / agent_id
            capability_dir = agent_dir / "capabilities" / capability_id
            capability_dir.mkdir(parents=True)
            (agent_dir / "agent.yaml").write_text(
                f"id: {agent_id}\nkind: specialist-agent\nname: Timeout Output Agent\nstatus: draft\n",
                encoding="utf-8",
            )
            (capability_dir / "capability.yaml").write_text(
                f"id: {agent_id}.{capability_id}\nkind: capability\nname: Sleep Runner\nstatus: draft\nentrypoint:\n  runner: runner.py\n",
                encoding="utf-8",
            )
            (capability_dir / "runner.py").write_text(
                "import time\nprint('before sleep')\ntime.sleep(2)\n",
                encoding="utf-8",
            )

            result = self.run_cli(
                "--json",
                "run",
                agent_id,
                capability_id,
                env={
                    "AI_DEVKIT_ROOT": str(test_root),
                    "AI_DEVKIT_RUN_TIMEOUT": "1",
                    "PATH": os.environ.get("PATH", ""),
                },
                replace_env=True,
            )

        self.assertEqual(result.returncode, 124, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "run")
        self.assertEqual(payload["schema_version"], "ai-devkit.run/v1")
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["agent_id"], agent_id)
        self.assertEqual(payload["capability_id"], capability_id)
        self.assertEqual(payload["returncode"], 124)
        self.assertEqual(payload["exit_code"], 124)
        self.assertIn("runner timed out", payload["error"])

    def test_doctor_fails_for_missing_root(self) -> None:
        result = subprocess.run(
            [sys.executable, str(AIKIT), "doctor", "--json"],
            cwd=ROOT,
            env=os.environ | {"AI_DEVKIT_ROOT": str(ROOT / "missing-aikit-root")},
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CLI_TIMEOUT_SECONDS,
        )

        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "doctor")
        self.assertEqual(payload["status"], "error")
        self.assertTrue(payload["errors"])

    def test_install_project_all_hosts_writes_host_artifacts_without_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as project_dir:
            result = self.run_cli(
                "--json",
                "install",
                "project",
                "--target",
                project_dir,
                "--host",
                "all",
                env={"PATH": os.environ.get("PATH", ""), "TOPDESK_PASSWORD": "leak-check-install"},
                replace_env=True,
            )
            project = Path(project_dir).resolve()
            codex_plugin = project / ".codex" / "plugins" / "ai-devkit" / ".codex-plugin" / "plugin.json"
            codex_skill = project / ".codex" / "skills" / "ai-devkit-router" / "SKILL.md"
            claude_plugin = project / ".claude" / "plugins" / "ai-devkit" / "plugin.json"
            claude_skill = project / ".claude" / "skills" / "ai-devkit-router" / "SKILL.md"
            claude_command = project / ".claude" / "commands" / "devkit-run.md"
            claude_subagent = project / ".claude" / "plugins" / "ai-devkit" / "agents" / "agent-devkit-db-analyst.md"
            claude_desktop_plugin = project / ".claude" / "plugins" / "ai-devkit-skill" / "plugin.json"
            claude_desktop_skill = project / ".claude" / "skills" / "ai-devkit" / "SKILL.md"
            project_lock = project / ".ai-devkit" / "ai-devkit.lock"

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["kind"], "install")
            self.assertEqual(payload["status"], "installed")
            self.assertEqual(payload["scope"], "project")
            self.assertEqual(payload["hosts"], ["codex", "claude-code", "claude-desktop"])
            self.assertFalse(payload["stored_secret"])
            self.assertIn(str(codex_plugin), payload["written"])
            self.assertIn(str(claude_plugin), payload["written"])
            self.assertIn(str(claude_desktop_plugin), payload["written"])
            self.assertTrue(codex_plugin.exists())
            self.assertTrue(codex_skill.exists())
            self.assertTrue(claude_plugin.exists())
            self.assertTrue(claude_skill.exists())
            self.assertTrue(claude_command.exists())
            self.assertTrue(claude_subagent.exists())
            self.assertTrue(claude_desktop_plugin.exists())
            self.assertTrue(claude_desktop_skill.exists())
            self.assertTrue(project_lock.exists())
            self.assertNotIn("leak-check-install", result.stdout)

    def test_install_project_writes_lock_with_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as project_dir:
            result = self.run_cli(
                "--json",
                "install",
                "project",
                "--target",
                project_dir,
                "--host",
                "codex",
                "--profiles",
                "sustentacao,infra",
            )
            lock_path = Path(project_dir).resolve() / ".ai-devkit" / "ai-devkit.lock"
            lock_text = lock_path.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["lock_path"], str(lock_path))
        self.assertIn(str(lock_path), payload["written"])
        self.assertIn("source: local", lock_text)
        self.assertIn("providers:", lock_text)
        self.assertIn("policy: project-overrides-global", lock_text)
        self.assertIn("- sustentacao", lock_text)
        self.assertIn("- infra", lock_text)

    def test_install_project_dry_run_does_not_write_files(self) -> None:
        with tempfile.TemporaryDirectory() as project_dir:
            result = self.run_cli(
                "--json",
                "install",
                "project",
                "--target",
                project_dir,
                "--host",
                "codex",
                "--dry-run",
            )
            project = Path(project_dir).resolve()
            codex_dir = project / ".codex"

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "planned")
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["hosts"], ["codex"])
            self.assertEqual(payload["written"], [])
            self.assertTrue(payload["planned"])
            self.assertIn(str(project / ".ai-devkit" / "ai-devkit.lock"), payload["planned"])
            self.assertFalse(codex_dir.exists())

    def test_install_missing_plugin_source_does_not_write_partial_lock(self) -> None:
        with tempfile.TemporaryDirectory() as fake_root, tempfile.TemporaryDirectory() as project_dir:
            result = self.run_cli(
                "--json",
                "install",
                "project",
                "--target",
                project_dir,
                "--host",
                "codex",
                env={"AI_DEVKIT_ROOT": fake_root, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )
            project = Path(project_dir).resolve()

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("install source not found", result.stderr)
            self.assertFalse((project / ".ai-devkit" / "config.yaml").exists())
            self.assertFalse((project / ".ai-devkit" / "ai-devkit.lock").exists())

    def test_install_global_uses_overridable_home(self) -> None:
        with tempfile.TemporaryDirectory() as install_home:
            result = self.run_cli(
                "--json",
                "install",
                "global",
                "--host",
                "codex",
                env={"AIKIT_INSTALL_HOME": install_home, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )
            home = Path(install_home).resolve()
            codex_plugin = home / ".codex" / "plugins" / "ai-devkit" / ".codex-plugin" / "plugin.json"
            codex_skill = home / ".codex" / "skills" / "ai-devkit-router" / "SKILL.md"
            runtime_config = home / ".agent-devkit" / "config.yaml"
            runtime_lock = home / ".agent-devkit" / "runtime.lock"
            bin_dir = home / ".agent-devkit" / "bin"
            agent_command = bin_dir / "agent"
            aikit_command = bin_dir / "aikit"
            ai_devkit_command = bin_dir / "ai-devkit"

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["kind"], "install")
            self.assertEqual(payload["scope"], "global")
            self.assertEqual(payload["target"], str(home))
            self.assertEqual(payload["hosts"], ["codex"])
            self.assertTrue(codex_plugin.exists())
            self.assertTrue(codex_skill.exists())
            self.assertTrue(runtime_config.exists())
            self.assertTrue(runtime_lock.exists())
            self.assertTrue(agent_command.exists())
            self.assertTrue(aikit_command.exists())
            self.assertTrue(ai_devkit_command.exists())
            self.assertEqual(payload["bin_dir"], str(bin_dir))
            self.assertEqual(payload["commands"]["agent"], str(agent_command))
            self.assertEqual(payload["lock_path"], str(runtime_lock))
            installed_agent = subprocess.run(
                [str(agent_command), "--version"],
                cwd=home,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=CLI_TIMEOUT_SECONDS,
                env={"PATH": os.environ.get("PATH", "")},
            )
            self.assertEqual(installed_agent.returncode, 0, installed_agent.stderr)
            self.assertIn("agent 0.1.7", installed_agent.stdout)

    def test_doctor_project_reports_lock_divergence(self) -> None:
        with tempfile.TemporaryDirectory() as install_home, tempfile.TemporaryDirectory() as project_dir:
            env = {"AIKIT_INSTALL_HOME": install_home, "PATH": os.environ.get("PATH", "")}
            global_install = self.run_cli(
                "--json",
                "install",
                "global",
                "--host",
                "codex",
                env=env,
                replace_env=True,
            )
            project_install = self.run_cli(
                "--json",
                "install",
                "project",
                "--target",
                project_dir,
                "--host",
                "codex",
                env=env,
                replace_env=True,
            )
            lock_path = Path(project_dir).resolve() / ".ai-devkit" / "ai-devkit.lock"
            lock_text = lock_path.read_text(encoding="utf-8").replace("commit: ", "commit: forced-divergence-", 1)
            lock_path.write_text(lock_text, encoding="utf-8")

            doctor = self.run_cli(
                "--json",
                "doctor",
                "--project",
                project_dir,
                env=env,
                replace_env=True,
            )

        self.assertEqual(global_install.returncode, 0, global_install.stderr)
        self.assertEqual(project_install.returncode, 0, project_install.stderr)
        self.assertEqual(doctor.returncode, 0, doctor.stderr)
        payload = json.loads(doctor.stdout)
        self.assertEqual(payload["kind"], "doctor")
        self.assertIn("locks", payload)
        self.assertEqual(payload["locks"]["status"], "diverged")
        self.assertTrue(payload["locks"]["global"]["exists"])
        self.assertTrue(payload["locks"]["project"]["exists"])
        self.assertTrue(any("lock divergence" in warning for warning in payload["warnings"]))

    def test_doctor_project_accepts_home_override_for_global_lock(self) -> None:
        with tempfile.TemporaryDirectory() as install_home, tempfile.TemporaryDirectory() as project_dir:
            global_install = self.run_cli(
                "--json",
                "install",
                "global",
                "--home",
                install_home,
                "--host",
                "codex",
            )
            project_install = self.run_cli(
                "--json",
                "install",
                "project",
                "--target",
                project_dir,
                "--host",
                "codex",
            )
            doctor = self.run_cli(
                "--json",
                "doctor",
                "--project",
                project_dir,
                "--home",
                install_home,
            )

        self.assertEqual(global_install.returncode, 0, global_install.stderr)
        self.assertEqual(project_install.returncode, 0, project_install.stderr)
        self.assertEqual(doctor.returncode, 0, doctor.stderr)
        payload = json.loads(doctor.stdout)
        self.assertTrue(payload["locks"]["global"]["exists"])
        self.assertEqual(payload["locks"]["global"]["path"], str(Path(install_home).resolve() / ".agent-devkit" / "runtime.lock"))

    def test_simple_lock_parser_reads_nested_host_lists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "ai-devkit.lock"
            lock_path.write_text(
                "\n".join(
                    [
                        "runtime:",
                        "  source: local",
                        "  commit: abc123",
                        "install:",
                        "  scope: project",
                        "  hosts:",
                        "    - codex",
                        "    - claude-code",
                        "profiles:",
                        "  - sustentacao",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            payload = read_simple_lock(lock_path)

        self.assertEqual(payload["install"]["hosts"], ["codex", "claude-code"])
        self.assertEqual(payload["profiles"], ["sustentacao"])

    def test_run_reports_missing_agent(self) -> None:
        result = self.run_cli("run", "missing-agent", "missing-capability")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("agent not found: missing-agent", result.stderr)

    def test_legacy_ai_devkit_entrypoint_still_works(self) -> None:
        result = subprocess.run(
            [sys.executable, str(AI_DEVKIT), "--json", "agents"],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CLI_TIMEOUT_SECONDS,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "agents")

    def test_legacy_ai_devkit_version_still_works(self) -> None:
        result = subprocess.run(
            [sys.executable, str(AI_DEVKIT), "--version"],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CLI_TIMEOUT_SECONDS,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ai-devkit 0.1.7", result.stdout)


if __name__ == "__main__":
    unittest.main()
