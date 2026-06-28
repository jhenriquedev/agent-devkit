#!/usr/bin/env python3
"""v0.1.5 contracts for agentic setup, local LLMs and governance."""

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

AGENT = ROOT / "agent"
CLI_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_CLI_TIMEOUT_SECONDS", "60"))


class BackendIdentityLeakHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API.
        self.rfile.read(int(self.headers.get("Content-Length", "0")))
        body = json.dumps({"choices": [{"message": {"content": "Meu nome e Claude, da Anthropic."}}]}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


class AgenticV015ContractsTest(unittest.TestCase):
    def run_agent(
        self,
        *args: str,
        env: dict[str, str] | None = None,
        replace_env: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        process_env = env or {} if replace_env else os.environ | (env or {})
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

    def fake_openai_server(self) -> tuple[http.server.HTTPServer, str]:
        server = http.server.HTTPServer(("127.0.0.1", 0), BackendIdentityLeakHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        return server, f"http://{host}:{port}/v1"

    def write_fake_ollama(self, directory: Path) -> Path:
        path = directory / "ollama"
        path.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import json, sys",
                    "args = sys.argv[1:]",
                    "if args == ['--version'] or args == ['version']:",
                    "    print('ollama version 0.9.0')",
                    "elif args == ['list']:",
                    "    print('NAME ID SIZE MODIFIED')",
                    "    print('qwen2.5-coder:latest abc 4.7GB 1 day ago')",
                    "elif args[:1] == ['pull']:",
                    "    print('pulled ' + (args[1] if len(args) > 1 else ''))",
                    "else:",
                    "    print(json.dumps({'ok': True, 'args': args}))",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        path.chmod(0o755)
        return path

    def test_missing_azure_source_returns_agentic_provider_wizard(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_agent(
                "--json",
                "analise",
                "o",
                "card",
                "7914",
                "do",
                "projeto",
                "sustentacao",
                "no",
                "azure",
                env={"AI_DEVKIT_CONFIG_HOME": tmpdir},
            )

        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "needs-input")
        self.assertEqual(payload["provider"], "azure-devops")
        self.assertEqual(payload["setup_wizard"]["status"], "waiting-for-user")
        self.assertEqual(payload["setup_wizard"]["next_question"]["id"], "azure_devops_opt_in")
        self.assertEqual(payload["setup_wizard"]["suggested_config"]["project"], "sustentacao")
        self.assertNotIn("azure-sustentacao", result.stdout)
        self.assertNotIn("agent source add", result.stdout)

    def test_missing_inferred_topdesk_provider_returns_global_configurator_wizard(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_agent(
                "--json",
                "run",
                "topdesk-orchestrator",
                "read-incident",
                "--number",
                "I 2606 001",
                env={"AI_DEVKIT_CONFIG_HOME": tmpdir, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "run")
        self.assertEqual(payload["status"], "partial")
        self.assertEqual(payload["setup_wizard"]["provider"], "topdesk")
        self.assertEqual(payload["setup_wizard"]["owner_agent"], "provider-configurator")
        question_ids = {item["id"] for item in payload["setup_wizard"]["questions"]}
        self.assertIn("topdesk_topdesk_base_url", question_ids)
        self.assertIn("topdesk_topdesk_username", question_ids)
        self.assertEqual(payload["next_question"]["id"], "topdesk_opt_in")

    def test_missing_explicit_elasticsearch_provider_returns_global_configurator_wizard(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_agent(
                "--json",
                "run",
                "elasticsearch-log-analyzer",
                "search-log-events",
                "--source",
                "prod",
                "--from",
                "2026-06-28T00:00:00Z",
                "--to",
                "2026-06-28T01:00:00Z",
                env={"AI_DEVKIT_CONFIG_HOME": tmpdir, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "run")
        self.assertEqual(payload["status"], "partial")
        self.assertEqual(payload["setup_wizard"]["provider"], "elasticsearch")
        self.assertEqual(payload["setup_wizard"]["owner_agent"], "provider-configurator")
        self.assertEqual(payload["next_question"]["id"], "elasticsearch_opt_in")
        self.assertFalse(any("agent provider configure" in step for step in payload["next_steps"]))

    def test_decisions_and_tools_can_be_managed_by_command_and_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            disabled = self.run_agent("tools", "disable", "azure-devops", "--json", env=env)
            listed = self.run_agent("decisions", "list", "--json", env=env)
            prompt_result = self.run_agent("--json", "reative", "o", "azure", "devops", env=env)

        self.assertEqual(disabled.returncode, 0, disabled.stderr)
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(prompt_result.returncode, 0, prompt_result.stderr)
        decisions = json.loads(listed.stdout)
        self.assertEqual(decisions["kind"], "decisions")
        self.assertEqual(decisions["items"][0]["state"], "disabled_by_user")
        payload = json.loads(prompt_result.stdout)
        self.assertEqual(payload["mode"], "control-center-route")
        self.assertEqual(payload["result"]["state"], "enabled")

    def test_natural_control_prompt_manages_catalogued_provider_tool_llm_and_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            topdesk = self.run_agent("--json", "desative", "topdesk", env=env)
            gh_cli = self.run_agent("--json", "habilite", "gh-cli", env=env)
            openrouter = self.run_agent("--json", "desative", "openrouter", env=env)
            skill = self.run_agent("--json", "desative", "a", "skill", "security-review", env=env)
            decisions = self.run_agent("decisions", "list", "--json", env=env)

        for result in (topdesk, gh_cli, openrouter, skill, decisions):
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(topdesk.stdout)["result"]["category"], "integrations")
        self.assertEqual(json.loads(topdesk.stdout)["result"]["id"], "topdesk")
        self.assertEqual(json.loads(gh_cli.stdout)["result"]["category"], "tools")
        self.assertEqual(json.loads(gh_cli.stdout)["result"]["id"], "gh-cli")
        self.assertEqual(json.loads(openrouter.stdout)["result"]["category"], "llms")
        self.assertEqual(json.loads(openrouter.stdout)["result"]["id"], "openrouter")
        self.assertEqual(json.loads(skill.stdout)["result"]["category"], "skills")
        self.assertEqual(json.loads(skill.stdout)["result"]["id"], "security-review")
        states = {(item["category"], item["id"]): item["state"] for item in json.loads(decisions.stdout)["items"]}
        self.assertEqual(states[("integrations", "topdesk")], "disabled_by_user")
        self.assertEqual(states[("tools", "gh-cli")], "enabled")
        self.assertEqual(states[("llms", "openrouter")], "disabled_by_user")
        self.assertEqual(states[("skills", "security-review")], "disabled_by_user")

    def test_natural_control_prompt_lists_categories_and_forgets_target_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            disabled = self.run_agent("--json", "desative", "anthropic", env=env)
            listed = self.run_agent("--json", "liste", "llms", env=env)
            forgot = self.run_agent("--json", "esqueca", "minha", "decisao", "sobre", "anthropic", env=env)
            decisions = self.run_agent("decisions", "list", "--json", env=env)

        self.assertEqual(disabled.returncode, 0, disabled.stderr)
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(forgot.returncode, 0, forgot.stderr)
        self.assertEqual(decisions.returncode, 0, decisions.stderr)
        listed_payload = json.loads(listed.stdout)
        self.assertEqual(listed_payload["mode"], "control-center-route")
        self.assertEqual(listed_payload["result"]["category"], "llms")
        self.assertIn("anthropic", {item["id"] for item in listed_payload["result"]["items"]})
        forgot_payload = json.loads(forgot.stdout)
        self.assertEqual(forgot_payload["result"]["action"], "forget")
        self.assertEqual(forgot_payload["result"]["removed"]["id"], "anthropic")
        self.assertEqual(json.loads(decisions.stdout)["items"], [])

    def test_natural_control_prompt_reports_unknown_and_ambiguous_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            unknown = self.run_agent("--json", "desative", "ferramenta-inexistente", env=env)
            ambiguous = self.run_agent("--json", "desative", "figma", env=env)

        self.assertEqual(unknown.returncode, 2, unknown.stderr)
        unknown_payload = json.loads(unknown.stdout)
        self.assertEqual(unknown_payload["status"], "needs-input")
        self.assertTrue(unknown_payload["unknown_control_target"])
        self.assertEqual(ambiguous.returncode, 2, ambiguous.stderr)
        ambiguous_payload = json.loads(ambiguous.stdout)
        self.assertEqual(ambiguous_payload["status"], "needs-input")
        self.assertTrue(ambiguous_payload["ambiguous_control_target"])
        self.assertGreaterEqual(len(ambiguous_payload["matches"]), 2)

    def test_natural_control_prompt_keeps_legacy_aliases_and_dry_run_has_no_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            azure = self.run_agent("--json", "desative", "azure", env=env)
            dry_run = self.run_agent("--dry-run", "--json", "desative", "openai", env=env)
            reset = self.run_agent("--json", "limpe", "decisoes", "de", "integracoes", env=env)
            decisions = self.run_agent("decisions", "list", "--json", env=env)

        self.assertEqual(azure.returncode, 0, azure.stderr)
        self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
        self.assertEqual(reset.returncode, 0, reset.stderr)
        self.assertEqual(decisions.returncode, 0, decisions.stderr)
        azure_payload = json.loads(azure.stdout)
        self.assertEqual(azure_payload["result"]["category"], "integrations")
        self.assertEqual(azure_payload["result"]["id"], "azure-devops")
        dry_payload = json.loads(dry_run.stdout)
        self.assertTrue(dry_payload["dry_run"])
        self.assertEqual(dry_payload["status"], "planned")
        self.assertEqual(dry_payload["result"]["category"], "llms")
        reset_payload = json.loads(reset.stdout)
        self.assertEqual(reset_payload["result"]["action"], "reset")
        self.assertEqual(reset_payload["result"]["category"], "integrations")
        self.assertEqual(json.loads(decisions.stdout)["items"], [])

    def test_ollama_status_models_and_pull_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as bindir:
            bin_path = Path(bindir)
            self.write_fake_ollama(bin_path)
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir, "PATH": f"{bin_path}{os.pathsep}{os.environ.get('PATH', '')}"}
            status = self.run_agent("ollama", "status", "--json", env=env)
            models = self.run_agent("ollama", "models", "--json", env=env)
            pull = self.run_agent("ollama", "pull", "qwen2.5-coder", "--yes", "--json", env=env)

        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(models.returncode, 0, models.stderr)
        self.assertEqual(pull.returncode, 0, pull.stderr)
        self.assertEqual(json.loads(status.stdout)["status"], "ok")
        self.assertEqual(json.loads(models.stdout)["items"][0]["name"], "qwen2.5-coder:latest")
        self.assertEqual(json.loads(pull.stdout)["status"], "ok")

    def test_toolchain_includes_ollama(self) -> None:
        result = self.run_agent("toolchain", "list", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        ids = {item["id"] for item in payload["items"]}
        self.assertIn("ollama", ids)

    def test_backend_identity_leak_is_rewritten_to_local_identity(self) -> None:
        server, base_url = self.fake_openai_server()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                env = {"AI_DEVKIT_CONFIG_HOME": tmpdir, "TEST_OPENAI_API_KEY": "secret"}
                configured = self.run_agent(
                    "llm",
                    "configure",
                    "openai",
                    "--api-key-env",
                    "TEST_OPENAI_API_KEY",
                    "--base-url",
                    base_url,
                    "--model",
                    "fake",
                    "--set-default",
                    "--json",
                    env=env,
                )
                result = self.run_agent("--json", "apresente-se", "brevemente", env=env)
        finally:
            server.shutdown()
            server.server_close()

        self.assertEqual(configured.returncode, 0, configured.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("Agent DevKit", payload["response"])
        self.assertNotIn("Claude", payload["response"])
        self.assertNotIn("Anthropic", payload["response"])

    def test_agent_dry_run_exposes_model_plan_and_review_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_agent(
                "--dry-run",
                "--json",
                "resuma",
                "logs",
                "longos",
                "e",
                "gere",
                "um",
                "documento",
                env={"AI_DEVKIT_CONFIG_HOME": tmpdir},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "planned")
        self.assertEqual(payload["model_plan"]["local_llm_role"], "operational-worker")
        self.assertTrue(payload["review_gate"]["required"])
        self.assertIn("claude-code", payload["review_gate"]["preferred_reviewers"])


if __name__ == "__main__":
    unittest.main()
