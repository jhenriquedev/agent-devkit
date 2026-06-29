#!/usr/bin/env python3
"""Contracts for controlled live module execution."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from cli.aikit.module_controller import run_module_controller


class ModuleControllerTest(unittest.TestCase):
    def test_controller_executes_allowed_safe_capability_and_audits_step(self) -> None:
        with isolated_home():
            result = run_module_controller(
                plan_with_task(write_policy="read_only"),
                load_agent=lambda agent_id: {"id": agent_id},
                run_capability=lambda agent, capability_id, args: {
                    "kind": "run",
                    "status": "ok",
                    "ok": True,
                    "reason": None,
                    "risks": [],
                    "next_steps": [],
                },
            )

        self.assertEqual(result["kind"], "module-controller-run")
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["ok"])
        self.assertEqual(result["stop_reason"], "success")
        self.assertEqual(len(result["steps"]), 1)
        self.assertEqual(result["steps"][0]["review"]["status"], "accepted")
        self.assertRegex(result["steps"][0]["audit_id"], r"^exec_")

    def test_controller_blocks_capability_outside_allowlist(self) -> None:
        with isolated_home():
            result = run_module_controller(
                plan_with_task(agent_id="other-agent", capability_id="unsafe", write_policy="read_only"),
                load_agent=lambda agent_id: {"id": agent_id},
                run_capability=lambda agent, capability_id, args: {"status": "ok", "ok": True},
            )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["stop_reason"], "blocked")
        self.assertIn("not allowed", result["blocked_tasks"][0]["reason"])

    def test_controller_blocks_non_autonomous_write_policy(self) -> None:
        with isolated_home():
            result = run_module_controller(
                plan_with_task(write_policy="confirm"),
                load_agent=lambda agent_id: {"id": agent_id},
                run_capability=lambda agent, capability_id, args: {"status": "ok", "ok": True},
            )

        self.assertEqual(result["status"], "blocked")
        self.assertIn("explicit confirmation", result["blocked_tasks"][0]["reason"])

    def test_controller_stops_when_no_primary_task_needs_input(self) -> None:
        result = run_module_controller(
            {"domain_agent": {"id": "task-orchestrator", "agent_mode": agent_mode()}, "specialist_tasks": []},
            load_agent=lambda agent_id: {"id": agent_id},
            run_capability=lambda agent, capability_id, args: {"status": "ok", "ok": True},
        )

        self.assertEqual(result["status"], "needs-input")
        self.assertEqual(result["stop_reason"], "no-primary-task")

    def test_controller_respects_disabled_capability_calls(self) -> None:
        mode = agent_mode()
        mode["can_call_capabilities"] = False
        result = run_module_controller(
            {"domain_agent": {"id": "task-orchestrator", "agent_mode": mode}, "specialist_tasks": []},
            load_agent=lambda agent_id: {"id": agent_id},
            run_capability=lambda agent, capability_id, args: {"status": "ok", "ok": True},
        )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["stop_reason"], "capability-calls-disabled")

    def test_controller_respects_autonomy_contract_needs_input(self) -> None:
        plan = plan_with_task(write_policy="read_only")
        plan["autonomy_contract"] = {
            "kind": "autonomy-contract",
            "schema_version": "ai-devkit.autonomy/v1",
            "level": 1,
            "level_id": "assisted",
            "status": "needs-input",
            "execution_allowed": False,
            "requires_human": True,
            "blockers": ["provider-configuration-required"],
        }
        result = run_module_controller(
            plan,
            load_agent=lambda agent_id: {"id": agent_id},
            run_capability=lambda agent, capability_id, args: {"status": "ok", "ok": True},
        )

        self.assertEqual(result["status"], "needs-input")
        self.assertEqual(result["stop_reason"], "needs-input")
        self.assertEqual(result["autonomy_contract"]["level_id"], "assisted")
        self.assertEqual(result["human_escalations"][0]["kind"], "autonomy-required-input")

    def test_controller_runs_collaborative_dependencies_and_sanitizes_handoff(self) -> None:
        calls = []

        def run_capability(agent: dict, capability_id: str, args: list[str]) -> dict:
            calls.append(capability_id)
            return {
                "kind": "run",
                "status": "ok",
                "ok": True,
                "stdout": f"collected evidence for {capability_id} SECRET=abc123",
                "risks": ["needs review"],
            }

        with isolated_home():
            result = run_module_controller(
                collaborative_plan(),
                load_agent=lambda agent_id: {"id": agent_id},
                run_capability=run_capability,
            )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(calls, ["configure-provider-source", "configure-provider-source"])
        self.assertEqual(result["steps"][1]["depends_on"], ["collect"])
        self.assertEqual(len(result["shared_context"]["facts"]), 3)
        self.assertEqual(len(result["shared_context"]["risks"]), 2)
        self.assertEqual(len(result["shared_context"]["handoffs"]), 2)
        self.assertEqual(result["shared_context"]["handoffs"][0]["from"], "provider-configurator")
        self.assertEqual(result["shared_context"]["handoffs"][0]["to"], "agent-devkit-core")
        self.assertEqual(result["shared_context"]["handoffs"][0]["confidence"], "high")
        self.assertNotIn("abc123", str(result["shared_context"]))

    def test_controller_escalates_when_specialist_limit_is_reached(self) -> None:
        plan = collaborative_plan()
        plan["domain_agent"]["agent_mode"]["max_specialists"] = 1

        with isolated_home():
            result = run_module_controller(
                plan,
                load_agent=lambda agent_id: {"id": agent_id},
                run_capability=lambda agent, capability_id, args: {"kind": "run", "status": "ok", "ok": True},
            )

        self.assertEqual(result["status"], "needs-input")
        self.assertEqual(result["stop_reason"], "needs-input")
        self.assertEqual(result["human_escalations"][0]["kind"], "max-specialists")


def plan_with_task(
    *,
    agent_id: str = "provider-configurator",
    capability_id: str = "configure-provider-source",
    write_policy: str,
) -> dict:
    return {
        "domain_agent": {"id": "task-orchestrator", "agent_mode": agent_mode()},
        "specialist_tasks": [
            {
                "id": f"{agent_id}.{capability_id}",
                "agent_id": agent_id,
                "capability_id": capability_id,
                "primary": True,
                "executable": True,
                "write_policy": write_policy,
                "args": [],
            }
        ],
    }


def agent_mode() -> dict:
    return {
        "type": "planner",
        "max_steps": 5,
        "max_specialists": 5,
        "max_llm_calls": 0,
        "timeout_seconds": 300,
        "can_call_capabilities": True,
        "can_call_llm": "optional",
        "can_request_user_input": True,
        "external_writes": False,
        "allowed_capabilities": ["provider-configurator/configure-provider-source"],
        "stop_conditions": ["success", "needs-input", "blocked", "max-steps"],
    }


def collaborative_plan() -> dict:
    mode = agent_mode()
    mode["stop_conditions"] = ["blocked", "max-steps"]
    return {
        "collaboration_enabled": True,
        "domain_agent": {"id": "task-orchestrator", "agent_mode": mode},
        "shared_context": {
            "facts": [{"source": "test", "summary": "initial"}],
            "inferences": [],
            "artifacts": [],
            "blockers": [],
            "decisions": [],
            "risks": [],
            "questions": [],
        },
        "specialist_tasks": [
            {
                "id": "provider-configurator.configure-provider-source.collect",
                "task_id": "collect",
                "agent_id": "provider-configurator",
                "capability_id": "configure-provider-source",
                "role": "collector",
                "depends_on": [],
                "primary": False,
                "executable": True,
                "write_policy": "read_only",
                "args": [],
            },
            {
                "id": "provider-configurator.configure-provider-source.analyze",
                "task_id": "analyze",
                "agent_id": "provider-configurator",
                "capability_id": "configure-provider-source",
                "role": "analyzer",
                "depends_on": ["collect"],
                "primary": False,
                "executable": True,
                "write_policy": "read_only",
                "args": [],
            },
        ],
    }


class isolated_home:
    def __enter__(self) -> Path:
        self.tmp = tempfile.TemporaryDirectory()
        self.old_env = os.environ.get("AI_DEVKIT_CONFIG_HOME")
        os.environ["AI_DEVKIT_CONFIG_HOME"] = self.tmp.name
        return Path(self.tmp.name)

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self.old_env is None:
            os.environ.pop("AI_DEVKIT_CONFIG_HOME", None)
        else:
            os.environ["AI_DEVKIT_CONFIG_HOME"] = self.old_env
        self.tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
