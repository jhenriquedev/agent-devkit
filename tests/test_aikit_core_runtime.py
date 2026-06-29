#!/usr/bin/env python3
"""Core runtime contracts independent from CLI argparse."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cli.aikit.core.requests import AgentPromptRequest, CapabilityRunRequest
from cli.aikit.core.runtime import (
    inspect_capability_request,
    list_agent_modules,
    list_capability_modules,
    run_agent_prompt,
    run_capability_request,
)


ROOT = Path(__file__).resolve().parents[1]


class AikitCoreRuntimeTest(unittest.TestCase):
    def test_agent_prompt_core_accepts_request_without_argparse(self) -> None:
        with tempfile.TemporaryDirectory() as config_home, mock.patch.dict(
            os.environ,
            {"AI_DEVKIT_CONFIG_HOME": config_home},
        ):
            payload = run_agent_prompt(
                AgentPromptRequest(
                    prompt="quem e voce?",
                    project=str(ROOT),
                    prog_name="agent",
                )
            )

        self.assertEqual(payload["kind"], "agent")
        self.assertEqual(payload["status"], "ok")
        self.assertFalse(payload["requires_llm"])
        self.assertEqual(payload["identity"]["name"], "Agent DevKit")

    def test_dry_run_prompt_core_returns_plan_without_llm(self) -> None:
        payload = run_agent_prompt(
            AgentPromptRequest(
                prompt="zzzz yyyyy sem rota conhecida",
                dry_run=True,
                project=str(ROOT),
            )
        )

        self.assertEqual(payload["kind"], "agent")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["requires_llm"])
        self.assertEqual(payload["execution_plan"]["kind"], "agentic-execution-plan")
        self.assertTrue(payload["execution_plan"]["controller_enabled"])
        self.assertEqual(payload["execution_plan"]["module_controller"]["mode"]["type"], "planner")

    def test_inventory_core_calls_return_structured_payloads(self) -> None:
        agents = list_agent_modules()
        capabilities = list_capability_modules("task-orchestrator")
        capability = inspect_capability_request("task-orchestrator", "plan-task")

        self.assertEqual(agents["kind"], "agents")
        task_orchestrator = next(item for item in agents["items"] if item["id"] == "task-orchestrator")
        self.assertEqual(task_orchestrator["agent_mode"]["type"], "planner")
        self.assertEqual(task_orchestrator["agent_mode"]["max_steps"], 5)
        self.assertEqual(task_orchestrator["agent_mode"]["max_specialists"], 3)
        self.assertEqual(task_orchestrator["agent_mode"]["max_llm_calls"], 1)
        self.assertEqual(capabilities["kind"], "capabilities")
        self.assertEqual(capabilities["agent"], "task-orchestrator")
        self.assertEqual(capability["kind"], "capability")
        self.assertEqual(capability["agent"]["id"], "task-orchestrator")
        self.assertEqual(capability["agent"]["agent_mode"]["type"], "planner")
        self.assertEqual(capability["capability"]["id"], "task-orchestrator.plan-task")

    def test_capability_run_core_uses_request_contract(self) -> None:
        payload = run_capability_request(
            CapabilityRunRequest(
                agent_id="task-orchestrator",
                capability_id="plan-task",
                capture_output=True,
                origin="mcp",
                request_id="req-123",
                inputs={"prompt": "planeje"},
            )
        )

        self.assertEqual(payload["kind"], "run")
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["origin"], "mcp")
        self.assertEqual(payload["request_id"], "req-123")
        self.assertEqual(payload["data"], {"prompt": "planeje"})
        self.assertEqual(payload["reason"], "missing_runner")
        self.assertEqual(payload["policy"]["canonical"], "read_only")
        self.assertEqual(payload["write_policy"], "read_only")
        self.assertEqual(payload["write_policy_raw"], "read_only")
        self.assertEqual(payload["write_policy_metadata"]["canonical"], "read_only")
        self.assertIn("capability has no runner", payload["error"])

    def test_core_requests_validate_host_input_shape(self) -> None:
        with self.assertRaisesRegex(ValueError, "prompt must be a string"):
            AgentPromptRequest(prompt=["nao", "permitido"])  # type: ignore[arg-type]

        with self.assertRaisesRegex(ValueError, "not a string"):
            CapabilityRunRequest(
                agent_id="task-orchestrator",
                capability_id="plan-task",
                capability_args="--bad",  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(ValueError, "origin must be one of"):
            CapabilityRunRequest(
                agent_id="task-orchestrator",
                capability_id="plan-task",
                origin="browser",  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(ValueError, "capture_output must be a boolean"):
            CapabilityRunRequest(
                agent_id="task-orchestrator",
                capability_id="plan-task",
                capture_output="yes",  # type: ignore[arg-type]
            )

        request = CapabilityRunRequest(
            agent_id="task-orchestrator",
            capability_id="plan-task",
            capability_args=["--dry-run"],
            source_id="local-source",
            dry_run=True,
        )
        self.assertEqual(request.capability_args, ("--dry-run",))
        self.assertEqual(request.source_id, "local-source")
        self.assertTrue(request.dry_run)

        empty_args_request = CapabilityRunRequest(
            agent_id="task-orchestrator",
            capability_id="plan-task",
            capability_args=None,  # type: ignore[arg-type]
        )
        self.assertEqual(empty_args_request.capability_args, ())


if __name__ == "__main__":
    unittest.main()
