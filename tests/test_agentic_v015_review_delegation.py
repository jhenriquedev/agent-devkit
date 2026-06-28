#!/usr/bin/env python3
"""Contracts for real local-LLM delegation and enforced review gates."""

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
AGENT = ROOT / "agent"
CLI_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_CLI_TIMEOUT_SECONDS", "60"))


class RecordingOpenAiHandler(http.server.BaseHTTPRequestHandler):
    response_text = "response"
    requests: list[dict[str, object]] = []

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API.
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {}
        self.__class__.requests.append({"path": self.path, "body": payload, "raw": raw})
        body = json.dumps({"choices": [{"message": {"content": self.__class__.response_text}}]}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


class AgenticReviewDelegationTest(unittest.TestCase):
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

    def fake_server(self, handler: type[RecordingOpenAiHandler]) -> tuple[http.server.HTTPServer, str]:
        handler.requests = []
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

    def test_operational_prompt_delegates_to_ollama_then_reviews_with_codex(self) -> None:
        class OllamaHandler(RecordingOpenAiHandler):
            response_text = "LOCAL SUMMARY: timeout errors grouped by request id."

        class CoordinatorHandler(RecordingOpenAiHandler):
            response_text = "FINAL ANSWER: use the grouped timeout summary."

        ollama_server, ollama_base_url = self.fake_server(OllamaHandler)
        coordinator_server, coordinator_base_url = self.fake_server(CoordinatorHandler)
        try:
            with tempfile.TemporaryDirectory() as config_home, tempfile.TemporaryDirectory() as bin_dir:
                fake_codex = self.write_fake_host_cli(Path(bin_dir), "codex", "REVIEW OK: final answer is supported.")
                env = {
                    "AI_DEVKIT_CONFIG_HOME": config_home,
                    "OPENAI_API_KEY": "test-openai-key",
                    "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}",
                }
                self.run_agent(
                    "llm",
                    "configure",
                    "ollama",
                    "--base-url",
                    ollama_base_url,
                    "--model",
                    "fake-ollama",
                    "--json",
                    env=env,
                )
                self.run_agent(
                    "llm",
                    "configure",
                    "openai",
                    "--api-key-env",
                    "OPENAI_API_KEY",
                    "--base-url",
                    coordinator_base_url,
                    "--model",
                    "fake-openai",
                    "--set-default",
                    "--json",
                    env=env,
                )
                self.run_agent(
                    "llm",
                    "configure",
                    "codex-cli",
                    "--command",
                    str(fake_codex),
                    "--json",
                    env=env,
                )
                result = self.run_agent("--json", "resuma", "texto", "operacional", "longo", "do", "sistema", env=env)
        finally:
            ollama_server.shutdown()
            ollama_server.server_close()
            coordinator_server.shutdown()
            coordinator_server.server_close()

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["llm_backend"], "openai")
        self.assertEqual(payload["local_llm_execution"]["status"], "ok")
        self.assertEqual(payload["local_llm_execution"]["agent_id"], "local-llm-operator")
        self.assertEqual(payload["local_llm_execution"]["llm_backend"], "ollama")
        self.assertEqual(payload["review_gate"]["status"], "reviewed")
        self.assertEqual(payload["review_result"]["status"], "ok")
        self.assertEqual(payload["review_result"]["llm_backend"], "codex-cli")
        self.assertTrue(OllamaHandler.requests)
        self.assertTrue(CoordinatorHandler.requests)
        coordinator_raw = str(CoordinatorHandler.requests[-1]["raw"])
        self.assertIn("LOCAL SUMMARY", coordinator_raw)

    def test_required_review_without_reviewer_blocks_completion(self) -> None:
        class CoordinatorHandler(RecordingOpenAiHandler):
            response_text = "FINAL DOCUMENT: planned content."

        coordinator_server, coordinator_base_url = self.fake_server(CoordinatorHandler)
        try:
            with tempfile.TemporaryDirectory() as config_home:
                env = {"AI_DEVKIT_CONFIG_HOME": config_home, "OPENAI_API_KEY": "test-openai-key"}
                self.run_agent(
                    "llm",
                    "configure",
                    "openai",
                    "--api-key-env",
                    "OPENAI_API_KEY",
                    "--base-url",
                    coordinator_base_url,
                    "--model",
                    "fake-openai",
                    "--set-default",
                    "--json",
                    env=env,
                )
                result = self.run_agent("--json", "crie", "um", "plano", "simples", env=env)
        finally:
            coordinator_server.shutdown()
            coordinator_server.server_close()

        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "needs-review")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["review_gate"]["status"], "needs-review")
        self.assertEqual(payload["review_result"]["status"], "needs-review")
        self.assertEqual(payload["review_task"]["status"], "needs-review")
        self.assertNotEqual(payload["review_gate"].get("status"), "reviewed")

    def test_review_blocked_decision_blocks_completion(self) -> None:
        class CoordinatorHandler(RecordingOpenAiHandler):
            response_text = "FINAL DOCUMENT: incomplete content."

        coordinator_server, coordinator_base_url = self.fake_server(CoordinatorHandler)
        try:
            with tempfile.TemporaryDirectory() as config_home, tempfile.TemporaryDirectory() as bin_dir:
                fake_codex = self.write_fake_host_cli(Path(bin_dir), "codex", "REVIEW BLOCKED: evidence is missing.")
                env = {
                    "AI_DEVKIT_CONFIG_HOME": config_home,
                    "OPENAI_API_KEY": "test-openai-key",
                    "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}",
                }
                self.run_agent(
                    "llm",
                    "configure",
                    "openai",
                    "--api-key-env",
                    "OPENAI_API_KEY",
                    "--base-url",
                    coordinator_base_url,
                    "--model",
                    "fake-openai",
                    "--set-default",
                    "--json",
                    env=env,
                )
                self.run_agent(
                    "llm",
                    "configure",
                    "codex-cli",
                    "--command",
                    str(fake_codex),
                    "--json",
                    env=env,
                )
                result = self.run_agent("--json", "crie", "um", "plano", "simples", env=env)
        finally:
            coordinator_server.shutdown()
            coordinator_server.server_close()

        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "needs-review")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["review_gate"]["status"], "needs-review")
        self.assertEqual(payload["review_result"]["status"], "blocked")
        self.assertEqual(payload["review_result"]["decision"], "blocked")
        self.assertEqual(payload["review_task"]["status"], "needs-review")

    def test_unstructured_review_decision_blocks_completion(self) -> None:
        class CoordinatorHandler(RecordingOpenAiHandler):
            response_text = "FINAL DOCUMENT: content to review."

        coordinator_server, coordinator_base_url = self.fake_server(CoordinatorHandler)
        try:
            with tempfile.TemporaryDirectory() as config_home, tempfile.TemporaryDirectory() as bin_dir:
                fake_codex = self.write_fake_host_cli(Path(bin_dir), "codex", "looks fine to me")
                env = {
                    "AI_DEVKIT_CONFIG_HOME": config_home,
                    "OPENAI_API_KEY": "test-openai-key",
                    "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}",
                }
                self.run_agent(
                    "llm",
                    "configure",
                    "openai",
                    "--api-key-env",
                    "OPENAI_API_KEY",
                    "--base-url",
                    coordinator_base_url,
                    "--model",
                    "fake-openai",
                    "--set-default",
                    "--json",
                    env=env,
                )
                self.run_agent(
                    "llm",
                    "configure",
                    "codex-cli",
                    "--command",
                    str(fake_codex),
                    "--json",
                    env=env,
                )
                result = self.run_agent("--json", "crie", "um", "plano", "simples", env=env)
        finally:
            coordinator_server.shutdown()
            coordinator_server.server_close()

        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "needs-review")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["review_gate"]["status"], "needs-review")
        self.assertEqual(payload["review_result"]["status"], "needs-review")
        self.assertEqual(payload["review_result"]["decision"], "unstructured")
        self.assertEqual(payload["review_task"]["status"], "needs-review")


if __name__ == "__main__":
    unittest.main()
