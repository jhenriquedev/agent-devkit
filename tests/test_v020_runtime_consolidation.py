#!/usr/bin/env python3
"""v0.2.0 runtime consolidation contracts."""

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


class RuntimeConsolidationV020Test(unittest.TestCase):
    def run_agent(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(AGENT), *args],
            cwd=ROOT,
            env=os.environ | (env or {}),
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CLI_TIMEOUT_SECONDS,
        )

    def json_agent(self, *args: str, env: dict[str, str] | None = None) -> dict[str, object]:
        result = self.run_agent(*args, "--json", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_roadmap_command_is_deterministic_and_filters_preteridos(self) -> None:
        payload = self.json_agent("roadmap")

        self.assertEqual(payload["kind"], "roadmap")
        self.assertEqual(payload["schema_version"], "agent-devkit.roadmap/v1")
        self.assertEqual(payload["version_scope"], "v0.2.0")
        active = set(payload["active_problems"])
        self.assertNotIn(25, active)
        self.assertNotIn(26, active)
        self.assertTrue(payload["phases"])

    def test_catalog_search_finds_agents_and_capabilities(self) -> None:
        payload = self.json_agent("catalog", "search", "pr")

        self.assertEqual(payload["kind"], "catalog")
        self.assertEqual(payload["action"], "search")
        self.assertEqual(payload["query"], "pr")
        self.assertTrue(payload["items"])
        self.assertTrue({item["type"] for item in payload["items"]} & {"agent", "capability"})
        for item in payload["items"]:
            self.assertIn("id", item)
            self.assertIn("path", item)
            self.assertIn("readiness", item)

    def test_agents_and_capabilities_search_show_aliases_use_catalog_contract(self) -> None:
        agents = self.json_agent("agents", "search", "pr")
        agent = self.json_agent("agents", "show", "github-pr-reviewer")
        capabilities = self.json_agent("capabilities", "search", "rls")

        self.assertEqual(agents["kind"], "catalog")
        self.assertEqual(agent["kind"], "catalog-item")
        self.assertEqual(agent["item"]["id"], "github-pr-reviewer")
        self.assertEqual(capabilities["kind"], "catalog")
        self.assertTrue(all(item["type"] == "capability" for item in capabilities["items"]))

    def test_route_explain_does_not_execute_capability(self) -> None:
        payload = self.json_agent("route", "explain", "revise as prs que recebi hoje")

        self.assertEqual(payload["kind"], "route-explain")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["execution"], "not-executed")
        self.assertTrue(payload["candidates"])
        self.assertIn(payload["decision"], {"selected", "needs-input"})
        self.assertIn("next_step", payload)

    def test_explain_accepts_global_json_before_flag(self) -> None:
        result = self.run_agent("--json", "--explain", "analise o card 9900")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "route-explain")
        self.assertEqual(payload["execution"], "not-executed")

    def test_route_explain_requires_capability_for_selected_decision(self) -> None:
        payload = self.json_agent("route", "explain", "revise as prs que recebi hoje")

        if not payload["selected"]["capability_id"]:
            self.assertEqual(payload["decision"], "needs-input")
            self.assertTrue(payload["will_use"]["human"])
            self.assertIn("capability", payload["next_step"].lower())

    def test_roadmap_phase_filters_problem_phase_map(self) -> None:
        payload = self.json_agent("roadmap", "phase", "7")

        self.assertEqual(payload["active_problems"], [28, 29])
        self.assertEqual(set(payload["problem_phase_map"]), {"28", "29"})

    def test_roadmap_preterido_problem_is_explicitly_out_of_scope(self) -> None:
        payload = self.json_agent("roadmap", "problem", "25")

        self.assertEqual(payload["active_problems"], [])
        self.assertEqual(payload["problem_phase_map"], {})
        self.assertEqual(payload["out_of_scope_problem"], 25)

    def test_catalog_short_query_does_not_match_arbitrary_substrings(self) -> None:
        payload = self.json_agent("catalog", "search", "pr")
        ids = {item["id"] for item in payload["items"]}

        self.assertIn("github-pr-reviewer", ids)
        self.assertNotIn("bpo-analyser", ids)
        self.assertNotIn("presentation-renderer", ids)

    def test_eval_and_prompt_injection_are_deterministic(self) -> None:
        suites = self.json_agent("eval", "list")
        routing = self.json_agent("eval", "run", "routing")
        injection = self.json_agent("eval", "run", "prompt-injection")

        self.assertEqual(suites["kind"], "eval-suites")
        self.assertIn("routing", {suite["id"] for suite in suites["suites"]})
        self.assertEqual(routing["kind"], "eval-run")
        self.assertEqual(routing["suite"], "routing")
        self.assertEqual(routing["status"], "passed")
        self.assertEqual(injection["suite"], "prompt-injection")
        self.assertEqual(injection["status"], "passed")

    def test_secrets_doctor_does_not_print_secret_values(self) -> None:
        env = {"SECRET_TOKEN": "super-secret-value"}
        payload = self.json_agent("secrets", "doctor", env=env)
        raw = json.dumps(payload, ensure_ascii=False)

        self.assertEqual(payload["kind"], "secrets-doctor")
        self.assertNotIn("super-secret-value", raw)
        self.assertTrue(payload["backends"])

    def test_local_workflow_and_contribution_mvp_commands(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            env = {"AI_DEVKIT_CONFIG_HOME": config_home}
            local = self.json_agent("local", "list", env=env)
            workflows = self.json_agent("workflow", "list", env=env)
            workflow = self.json_agent("workflow", "install", "daily-pr-review", "--dry-run", env=env)
            contribution = self.json_agent("contribution", "checklist", "missing-extension", env=env)

        self.assertEqual(local["kind"], "local-extensions")
        self.assertEqual(workflows["kind"], "workflows")
        self.assertEqual(workflow["kind"], "workflow-install")
        self.assertEqual(workflow["mode"], "dry-run")
        self.assertEqual(contribution["kind"], "contribution-checklist")
        self.assertEqual(contribution["status"], "blocked")

    def test_mcp_v2_tools_are_exposed(self) -> None:
        payload = self.json_agent("mcp", "tools")
        names = {tool["name"] for tool in payload["tools"]}

        self.assertGreaterEqual(
            names,
            {
                "agent_devkit_catalog_search",
                "agent_devkit_route_explain",
                "agent_devkit_eval_list",
                "agent_devkit_eval_run",
                "agent_devkit_secrets_doctor",
                "agent_devkit_roadmap",
            },
        )


if __name__ == "__main__":
    unittest.main()
