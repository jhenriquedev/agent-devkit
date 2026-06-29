#!/usr/bin/env python3
"""Agentic provider setup wizard contracts."""

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
AGENT = ROOT / "agent"
CLI_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_CLI_TIMEOUT_SECONDS", "60"))

from cli.aikit.configuration_orchestrator import provider_setup_wizard


class AgenticWizardFlowTest(unittest.TestCase):
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

    def test_missing_source_creates_persistent_provider_wizard(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            env = {"AI_DEVKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")}
            result = self.run_agent(
                "--json",
                "analise",
                "o",
                "card",
                "9900",
                "do",
                "projeto",
                "sustentacao",
                "no",
                "azure",
                env=env,
                replace_env=True,
            )

            self.assertEqual(result.returncode, 2, result.stderr)
            payload = json.loads(result.stdout)
            wizard = payload["setup_wizard"]
            wizard_id = wizard["wizard_id"]
            self.assertEqual(wizard["status"], "waiting-for-user")
            self.assertEqual(wizard["next_question"]["id"], "azure_devops_opt_in")
            self.assertTrue((Path(config_home) / "state" / "wizards" / f"{wizard_id}.json").exists())

            show = self.run_agent("wizard", "--json", "show", wizard_id, env=env, replace_env=True)

            self.assertEqual(show.returncode, 0, show.stderr)
            shown = json.loads(show.stdout)
            self.assertEqual(shown["wizard"]["wizard_id"], wizard_id)
            self.assertEqual(shown["wizard"]["provider"], "azure-devops")

    def test_denying_provider_wizard_persists_user_decision(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            env = {"AI_DEVKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")}
            created = self.run_agent(
                "--json",
                "analise",
                "o",
                "card",
                "9901",
                "do",
                "projeto",
                "sustentacao",
                "no",
                "azure",
                env=env,
                replace_env=True,
            )
            wizard_id = json.loads(created.stdout)["setup_wizard"]["wizard_id"]

            denied = self.run_agent("wizard", "--json", "answer", wizard_id, "nao", env=env, replace_env=True)
            decisions = self.run_agent("decisions", "--json", "list", "--category", "tools", env=env, replace_env=True)

            self.assertEqual(denied.returncode, 0, denied.stderr)
            payload = json.loads(denied.stdout)
            self.assertEqual(payload["wizard"]["status"], "denied-by-user")
            self.assertFalse(payload["stored_secret"])
            states = {(item["category"], item["id"]): item["state"] for item in json.loads(decisions.stdout)["items"]}
            self.assertEqual(states[("tools", "azure-devops")], "denied_by_user")

    def test_answering_provider_wizard_creates_source_and_resumes_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            env = {
                "AI_DEVKIT_CONFIG_HOME": config_home,
                "PATH": os.environ.get("PATH", ""),
                "AZURE_DEVOPS_PAT": "test-pat-not-stored",
            }
            created = self.run_agent(
                "--json",
                "analise",
                "o",
                "card",
                "9902",
                "do",
                "projeto",
                "sustentacao",
                "no",
                "azure",
                env=env,
                replace_env=True,
            )
            wizard_id = json.loads(created.stdout)["setup_wizard"]["wizard_id"]

            answers = ["sim", "example-org", "sustentacao", "7.1", "env", "AZURE_DEVOPS_PAT", "azure-sustentacao", "sim"]
            payload = None
            for answer in answers:
                result = self.run_agent("wizard", "--json", "answer", wizard_id, answer, env=env, replace_env=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)

            assert payload is not None
            self.assertEqual(payload["wizard"]["status"], "completed")
            self.assertEqual(payload["source_result"]["status"], "configured")
            self.assertTrue(payload["resumed_prompt"])
            self.assertIn("resume_result", payload)
            self.assertFalse(payload["stored_secret"])
            serialized = json.dumps(payload, ensure_ascii=False)
            self.assertNotIn("test-pat-not-stored", serialized)

            sources = self.run_agent("source", "--json", "list", env=env, replace_env=True)
            source_items = {item["id"]: item for item in json.loads(sources.stdout)["items"]}
            self.assertIn("azure-sustentacao", source_items)
            self.assertEqual(source_items["azure-sustentacao"]["env_refs"]["AZURE_DEVOPS_PAT"], "AZURE_DEVOPS_PAT")

    def test_wizard_rejects_raw_secret_before_persisting_answer(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            env = {"AI_DEVKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")}
            created = self.run_agent(
                "--json",
                "analise",
                "o",
                "card",
                "9903",
                "do",
                "projeto",
                "sustentacao",
                "no",
                "azure",
                env=env,
                replace_env=True,
            )
            wizard_id = json.loads(created.stdout)["setup_wizard"]["wizard_id"]
            for answer in ["sim", "example-org", "sustentacao", "7.1", "env"]:
                step = self.run_agent("wizard", "--json", "answer", wizard_id, answer, env=env, replace_env=True)
                self.assertEqual(step.returncode, 0, step.stderr)

            rejected = self.run_agent("wizard", "--json", "answer", wizard_id, "sk-abcdefghijklmnop", env=env, replace_env=True)

            self.assertEqual(rejected.returncode, 1)
            state_path = Path(config_home) / "state" / "wizards" / f"{wizard_id}.json"
            state_text = state_path.read_text(encoding="utf-8")
            self.assertNotIn("sk-abcdefghijklmnop", state_text)

    def test_provider_wizard_secret_config_field_requests_env_ref(self) -> None:
        wizard = provider_setup_wizard(ROOT, "bpo")
        question = next(
            item
            for item in wizard["questions"]
            if item.get("env_ref_key") == "BPO_FORBIDDEN_URL_PATTERNS"
        )

        self.assertTrue(question["secret"])
        self.assertFalse(question["stores_secret"])
        self.assertNotIn("config_key", question)
        self.assertEqual(question["suggested_value"], "BPO_FORBIDDEN_URL_PATTERNS")

    def test_wizard_no_run_flag_can_be_used_after_answer(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            env = {
                "AI_DEVKIT_CONFIG_HOME": config_home,
                "PATH": os.environ.get("PATH", ""),
                "AZURE_DEVOPS_PAT": "test-pat-not-stored",
            }
            created = self.run_agent(
                "--json",
                "analise",
                "o",
                "card",
                "9904",
                "do",
                "projeto",
                "sustentacao",
                "no",
                "azure",
                env=env,
                replace_env=True,
            )
            wizard_id = json.loads(created.stdout)["setup_wizard"]["wizard_id"]
            for answer in ["sim", "example-org", "sustentacao", "7.1", "env", "AZURE_DEVOPS_PAT", "azure-sustentacao"]:
                step = self.run_agent("wizard", "--json", "answer", wizard_id, answer, env=env, replace_env=True)
                self.assertEqual(step.returncode, 0, step.stderr)

            final = self.run_agent("wizard", "answer", wizard_id, "sim", "--no-run", "--json", env=env, replace_env=True)

            self.assertEqual(final.returncode, 0, final.stderr)
            payload = json.loads(final.stdout)
            self.assertEqual(payload["wizard"]["status"], "completed")
            self.assertFalse(payload["resumed_prompt"])
            self.assertNotIn("resume_result", payload)


if __name__ == "__main__":
    unittest.main()
