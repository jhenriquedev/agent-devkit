#!/usr/bin/env python3
"""v0.1.5 multi-agent orchestration contracts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cli.aikit.agent_registry import load_agent_registry

AGENT = ROOT / "agent"
CLI_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_CLI_TIMEOUT_SECONDS", "60"))


class AgenticMultiAgentContractsTest(unittest.TestCase):
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

    def write_card_fixture(self, path: Path, *, card_id: int) -> Path:
        path.write_text(
            json.dumps(
                {
                    "work_item": {
                        "id": card_id,
                        "fields": {
                            "System.Title": f"Falha no card {card_id}",
                            "System.State": "Active",
                            "System.WorkItemType": "Bug",
                            "System.AssignedTo": {"displayName": "Analista"},
                            "System.Description": "Erro intermitente na operacao.",
                        },
                        "comments": [{"text": "Cliente relata falha recorrente."}],
                        "url": f"https://dev.azure.com/example/project/_workitems/edit/{card_id}",
                    }
                }
            ),
            encoding="utf-8",
        )
        return path

    def write_fake_host_cli(self, path: Path, response: str) -> Path:
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

    def test_dry_run_card_prompt_returns_multiagent_execution_plan(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_agent(
                "--dry-run",
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
                env={"AI_DEVKIT_CONFIG_HOME": config_home},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        plan = payload["execution_plan"]
        self.assertEqual(plan["kind"], "agentic-execution-plan")
        self.assertEqual(plan["status"], "planned")
        self.assertEqual(plan["routing_decision"]["confidence_label"], "high")
        self.assertIn("deterministic", plan["routing_decision"]["reason"])
        self.assertIn("policy_summary", plan)
        self.assertGreaterEqual(plan["policy_summary"]["autonomous_safe"], 1)
        self.assertEqual(plan["coordinator_agent"]["id"], "task-orchestrator")
        self.assertIn("azure-devops-orchestrator", {task["agent_id"] for task in plan["specialist_tasks"]})
        self.assertEqual(plan["review_task"]["agent_id"], "execution-reviewer")
        self.assertEqual(plan["review_task"]["write_policy_metadata"]["canonical"], "read_only")
        self.assertTrue(plan["configuration_tasks"])
        self.assertEqual(plan["configuration_tasks"][0]["agent_id"], "provider-configurator")
        self.assertEqual(plan["configuration_tasks"][0]["provider"], "azure-devops")
        self.assertEqual(plan["configuration_tasks"][0]["write_policy_metadata"]["canonical"], "local_config_write")
        primary = next(task for task in plan["specialist_tasks"] if task["agent_id"] == "azure-devops-orchestrator")
        self.assertEqual(primary["write_policy_metadata"]["canonical"], primary["write_policy"])
        self.assertEqual(primary["role"], "collector")
        self.assertEqual(primary["task_id"], primary["id"])
        self.assertIn("collaboration_graph", plan)
        self.assertTrue(plan["collaboration_enabled"])
        self.assertGreaterEqual(len(plan["collaboration_graph"]["nodes"]), 1)
        self.assertEqual(plan["shared_context"]["schema_version"], "ai-devkit.collaboration/v1")
        self.assertEqual(plan["execution_model"]["schema_version"], "ai-devkit.execution-model/v1")
        self.assertEqual(plan["execution_model"]["decision_owner"], "agent-devkit-core")
        self.assertEqual(plan["execution_model"]["coordinator"], "task-orchestrator")
        self.assertEqual(plan["execution_model"]["limits"]["max_specialists"], 1)
        self.assertEqual(plan["autonomy_contract"]["schema_version"], "ai-devkit.autonomy/v1")
        self.assertEqual(plan["autonomy_contract"]["level_id"], "assisted")
        self.assertFalse(plan["autonomy_contract"]["execution_allowed"])
        self.assertTrue(plan["autonomy_contract"]["requires_human"])
        self.assertEqual(plan["execution_model"]["autonomy_level_id"], "assisted")
        self.assertFalse(plan["execution_model"]["execution_allowed"])
        self.assertEqual(plan["stop_conditions"], plan["execution_model"]["stop_conditions"])
        self.assertIn("task_id", plan["trace"][1])
        self.assert_plan_agent_ids_are_registered(plan)
        registry = load_agent_registry(ROOT)
        self.assertEqual(registry["runtime_roles"]["coordinator"], "task-orchestrator")
        self.assertEqual(registry["runtime_roles"]["provider-configurator"], "provider-configurator")
        self.assertEqual(registry["runtime_roles"]["local-worker"], "local-llm-operator")
        self.assertEqual(registry["runtime_roles"]["reviewer"], "execution-reviewer")
        self.assertIn("task-orchestrator/plan-task", registry["capabilities"])
        self.assertIn("provider-configurator/configure-provider-source", registry["capabilities"])
        self.assertIn("local-llm-operator/select-local-worker", registry["capabilities"])
        self.assertIn("execution-reviewer/review-final-output", registry["capabilities"])
        read_card = registry["capabilities"]["azure-devops-orchestrator/read-card"]
        self.assertEqual(read_card["source_contract"]["origin"], "runtime.source")
        self.assertTrue(read_card["source_contract"]["enabled"])
        self.assertEqual(read_card["provider_resolution"]["source"], "runtime")

    def test_missing_card_source_preserves_wizard_inside_multiagent_plan(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
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
                env={"AI_DEVKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        plan = payload["execution_plan"]
        self.assertEqual(payload["status"], "needs-input")
        self.assertEqual(plan["status"], "needs-input")
        self.assertEqual(plan["model_plan"]["strategy"], "human")
        self.assertEqual(plan["execution_model"]["model_strategy"], "human")
        self.assertEqual(plan["autonomy_contract"]["level_id"], "assisted")
        self.assertIn("provider-configuration-required", plan["autonomy_contract"]["blockers"])
        self.assertEqual(plan["execution_model"]["limits"]["max_llm_calls"], 0)
        self.assertFalse(plan["execution_model"]["allowed_side_effects"]["can_call_llm"])
        self.assertEqual(plan["configuration_tasks"][0]["agent_id"], "provider-configurator")
        self.assertEqual(plan["configuration_tasks"][0]["setup_wizard"]["next_question"]["id"], "azure_devops_opt_in")
        self.assertEqual(payload["setup_wizard"]["next_question"]["id"], "azure_devops_opt_in")
        self.assertIn("provider-configurator", [item["agent_id"] for item in payload["orchestration_trace"]])

    def test_n1_prompt_uses_n1_coordinator_and_declared_specialists(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_agent(
                "--dry-run",
                "--json",
                "execute",
                "triagem",
                "n1",
                "do",
                "card",
                "7914",
                env={"AI_DEVKIT_CONFIG_HOME": config_home},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)["execution_plan"]
        self.assertEqual(plan["domain_agent"]["id"], "n1-support-agent")
        specialist_pairs = {(task["agent_id"], task["capability_id"]) for task in plan["specialist_tasks"]}
        self.assertIn(("azure-devops-orchestrator", "read-card"), specialist_pairs)
        self.assertIn(("topdesk-orchestrator", "read-incident"), specialist_pairs)
        self.assertIn(("sqlserver-data-analyzer", "run-readonly-query"), specialist_pairs)

    def test_prompt_router_selects_non_card_specialist_from_registry(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_agent(
                "--dry-run",
                "--json",
                "analise",
                "logs",
                "do",
                "cloudwatch",
                "para",
                "erro",
                "no",
                "servico",
                "checkout",
                env={"AI_DEVKIT_CONFIG_HOME": config_home},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)["execution_plan"]
        routing = plan["routing_decision"]
        self.assertEqual(routing["status"], "selected")
        self.assertEqual(routing["method"], "manifest-routing")
        self.assertEqual(routing["confidence_label"], "high")
        self.assertIn("aws-cloudwatch-log-analyzer", routing["reason"])
        self.assertTrue(routing["alternatives"])
        self.assertEqual(routing["selected_agent_id"], "aws-cloudwatch-log-analyzer")
        self.assertEqual(routing["selected_capability_id"], "analyze-service-error")
        self.assertIn("cloudwatch", routing["candidates"][0]["matched_anchors"])
        self.assertIn("cloudwatch", routing["candidates"][0]["selected_capability_matched_anchors"])
        self.assertEqual(plan["domain_agent"]["id"], "aws-cloudwatch-log-analyzer")
        self.assertIn("aws-cloudwatch-log-analyzer", {task["agent_id"] for task in plan["specialist_tasks"]})
        self.assertIn("aws", {task["provider"] for task in plan["configuration_tasks"]})

    def test_non_card_provider_prompt_requests_configuration_before_llm(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_agent(
                "--json",
                "analise",
                "logs",
                "do",
                "cloudwatch",
                "para",
                "erro",
                "no",
                "servico",
                "checkout",
                env={"AI_DEVKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "needs-input")
        self.assertEqual(payload["provider"], "aws")
        self.assertFalse(payload.get("requires_llm", False))
        self.assertEqual(payload["setup_wizard"]["owner_agent"], "provider-configurator")
        self.assertEqual(payload["execution_plan"]["domain_agent"]["id"], "aws-cloudwatch-log-analyzer")
        self.assertEqual(payload["execution_plan"]["routing_decision"]["method"], "manifest-routing")

    def test_prompt_router_selects_document_specialist_from_registry(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_agent(
                "--dry-run",
                "--json",
                "gere",
                "uma",
                "especificacao",
                "tecnica",
                "para",
                "essa",
                "demanda",
                env={"AI_DEVKIT_CONFIG_HOME": config_home},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)["execution_plan"]
        routing = plan["routing_decision"]
        self.assertEqual(routing["status"], "selected")
        self.assertEqual(routing["method"], "manifest-routing")
        self.assertEqual(routing["confidence_label"], "high")
        self.assertIn("software-specification-analyst", routing["reason"])
        self.assertEqual(routing["selected_agent_id"], "software-specification-analyst")
        self.assertEqual(routing["selected_capability_id"], "create-technical-spec")
        self.assertIn("spec.technical", routing["candidates"][0]["selected_capability_matched_intents"])
        self.assertEqual(plan["domain_agent"]["id"], "software-specification-analyst")
        self.assertIn(
            ("software-specification-analyst", "create-technical-spec"),
            {(task["agent_id"], task["capability_id"]) for task in plan["specialist_tasks"]},
        )

    def test_generic_prompt_uses_orchestrator_without_self_specialist_task(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_agent(
                "--dry-run",
                "--json",
                "zzzz",
                "yyyyy",
                "sem",
                "rota",
                "conhecida",
                env={"AI_DEVKIT_CONFIG_HOME": config_home},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)["execution_plan"]
        self.assertEqual(plan["routing_decision"]["status"], "no-match")
        self.assertEqual(plan["routing_decision"]["confidence_label"], "low")
        self.assertIn("No manifest routing candidate", plan["routing_decision"]["reason"])
        self.assertEqual(plan["coordinator_agent"]["id"], "task-orchestrator")
        self.assertEqual(plan["domain_agent"]["id"], "task-orchestrator")
        self.assertTrue(plan["controller_enabled"])
        self.assertEqual(plan["module_controller"]["mode"]["type"], "planner")
        self.assertNotIn("task-orchestrator", {task["agent_id"] for task in plan["specialist_tasks"]})
        self.assert_plan_agent_ids_are_registered(plan)

    def test_ambiguous_database_prompt_requests_routing_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_agent(
                "--json",
                "analise",
                "banco",
                "sql",
                env={"AI_DEVKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        plan = payload["execution_plan"]
        routing = payload["routing_decision"]
        self.assertEqual(payload["status"], "needs-input")
        self.assertEqual(payload["mode"], "agentic-routing")
        self.assertTrue(payload["requires_routing_confirmation"])
        self.assertEqual(plan["status"], "needs-input")
        self.assertEqual(plan["domain_agent"]["id"], "task-orchestrator")
        self.assertEqual(routing["status"], "ambiguous")
        self.assertEqual(routing["method"], "manifest-routing")
        self.assertEqual(routing["confidence_label"], "medium")
        self.assertTrue(routing["requires_confirmation"])
        self.assertIn("Multiple routing candidates", routing["reason"])
        self.assertTrue(routing["question"])
        self.assertGreaterEqual(len(routing["options"]), 2)
        self.assertTrue(routing["alternatives"])
        self.assertIsNone(routing["selected_agent_id"])
        self.assertFalse(plan["specialist_tasks"])
        self.assertFalse(plan["configuration_tasks"])
        self.assertIn("postgres-data-analyzer", {item["agent_id"] for item in routing["candidates"]})
        self.assertIn("sqlserver-data-analyzer", {item["agent_id"] for item in routing["candidates"]})

    def test_ambiguous_database_dry_run_exposes_routing_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            result = self.run_agent(
                "--dry-run",
                "--json",
                "analise",
                "banco",
                "sql",
                env={"AI_DEVKIT_CONFIG_HOME": config_home, "PATH": os.environ.get("PATH", "")},
                replace_env=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["requires_routing_confirmation"])
        self.assertEqual(payload["routing_decision"]["status"], "ambiguous")
        self.assertTrue(payload["matches"])
        self.assertIn("confirmacao", payload["response"])

    def test_card_prompt_with_source_executes_through_multiagent_plan(self) -> None:
        with tempfile.TemporaryDirectory() as config_home, tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.write_card_fixture(Path(tmpdir) / "card-9901.json", card_id=9901)
            fake_codex = self.write_fake_host_cli(Path(tmpdir) / "codex", "REVIEW OK: card analysis is supported.")
            env = {"AI_DEVKIT_CONFIG_HOME": config_home, "PATH": f"{tmpdir}:{os.environ.get('PATH', '')}"}
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
                "analise",
                "o",
                "card",
                "9901",
                "no",
                "azure",
                env=env,
                replace_env=True,
            )

        self.assertEqual(configure.returncode, 0, configure.stderr)
        self.assertEqual(reviewer.returncode, 0, reviewer.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["mode"], "agentic-route")
        self.assertEqual(payload["execution_plan"]["status"], "ok")
        self.assertEqual(payload["execution_plan"]["executed_tasks"][0]["agent_id"], "azure-devops-orchestrator")
        self.assertEqual(payload["execution_plan"]["executed_tasks"][0]["write_policy_metadata"]["canonical"], "read_only")
        self.assertIn("# Card Analysis", payload["response"])
        self.assertIn("- ID: 9901", payload["response"])
        self.assertEqual(payload["review_task"]["status"], "reviewed")
        self.assertEqual(payload["review_result"]["status"], "ok")
        self.assertEqual(payload["review_result"]["llm_backend"], "codex-cli")
        self.assertIn("azure-devops-orchestrator", [item["agent_id"] for item in payload["orchestration_trace"]])
        self.assert_plan_agent_ids_are_registered(payload["execution_plan"])

    def test_card_prompt_marks_review_task_needs_review_when_reviewer_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as config_home, tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.write_card_fixture(Path(tmpdir) / "card-9902.json", card_id=9902)
            fake_codex = self.write_fake_host_cli(Path(tmpdir) / "codex", "REVIEW BLOCKED: missing evidence.")
            env = {"AI_DEVKIT_CONFIG_HOME": config_home, "PATH": f"{tmpdir}:{os.environ.get('PATH', '')}"}
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
                "analise",
                "o",
                "card",
                "9902",
                "no",
                "azure",
                env=env,
                replace_env=True,
            )

        self.assertEqual(configure.returncode, 0, configure.stderr)
        self.assertEqual(reviewer.returncode, 0, reviewer.stderr)
        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "needs-review")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["review_gate"]["status"], "needs-review")
        self.assertEqual(payload["review_result"]["status"], "blocked")
        self.assertEqual(payload["review_task"]["status"], "needs-review")
        self.assertEqual(payload["execution_plan"]["review_task"]["status"], "needs-review")

    def assert_plan_agent_ids_are_registered(self, plan: dict[str, Any]) -> None:
        registry = load_agent_registry(ROOT)
        known_agents = set(registry["agents"])
        emitted: set[str] = set()
        for key in ("coordinator_agent", "domain_agent"):
            value = plan.get(key)
            if isinstance(value, dict) and value.get("id"):
                emitted.add(str(value["id"]))
            if isinstance(value, dict) and value.get("agent_id"):
                emitted.add(str(value["agent_id"]))
        review_task = plan.get("review_task")
        if isinstance(review_task, dict) and review_task.get("agent_id"):
            emitted.add(str(review_task["agent_id"]))
        for key in ("specialist_tasks", "configuration_tasks", "executed_tasks", "blocked_tasks", "trace"):
            for item in plan.get(key) or []:
                if isinstance(item, dict) and item.get("agent_id"):
                    emitted.add(str(item["agent_id"]))
        self.assertFalse(emitted - known_agents, f"agent ids missing from agents/: {sorted(emitted - known_agents)}")


if __name__ == "__main__":
    unittest.main()
