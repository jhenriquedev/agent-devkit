#!/usr/bin/env python3
"""Tests for automation-architect runners and repository."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

from cli.aikit.orchestrator import build_execution_plan


ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "agent"
AGENT_DIR = ROOT / "agents" / "automation-architect"
REPOSITORY_PATH = AGENT_DIR / "infra" / "integrations" / "automation-architecture" / "automation_architecture_repository.py"


def load_repository_class():
    spec = importlib.util.spec_from_file_location("automation_architecture_repository", REPOSITORY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load automation architecture repository")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.AutomationArchitectureRepository


AutomationArchitectureRepository = load_repository_class()


class AutomationArchitectTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = AutomationArchitectureRepository()

    def test_classifies_api_and_file_automation_as_python(self) -> None:
        result = self.repository.classify_automation_request(
            request="Automatize a coleta via API REST e salve o resultado em CSV local."
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["automation_type"], "python")
        self.assertEqual(result["recommended_agent"], "python-automation-builder")
        self.assertTrue(result["available_delegate"])

    def test_explicit_selenium_requirement_wins_over_generic_web(self) -> None:
        result = self.repository.classify_automation_request(
            request="Automatize login web legado usando Selenium WebDriver e grid."
        )

        self.assertEqual(result["automation_type"], "selenium")
        self.assertEqual(result["recommended_capability"], "plan-selenium-automation")

    def test_web_without_api_recommends_playwright_builder(self) -> None:
        result = self.repository.classify_automation_request(
            request="Automatize preenchimento de formulario em site sem API documentada."
        )

        self.assertEqual(result["automation_type"], "playwright")
        self.assertTrue(result["available_delegate"])
        self.assertEqual(result["recommended_agent"], "playwright-automation-builder")
        self.assertEqual(result["recommended_capability"], "plan-playwright-automation")

    def test_desktop_visual_automation_requires_confirmation(self) -> None:
        result = self.repository.classify_automation_request(
            request="Automatize cliques na janela desktop com mouse e screenshots."
        )

        self.assertEqual(result["automation_type"], "pyautogui")
        self.assertTrue(result["requires_confirmation"])
        self.assertIn("desktop visual automation is fragile and must be a last resort", result["risks"])

    def test_delegation_is_manual_contract_only(self) -> None:
        result = self.repository.delegate_automation_build(
            request="Automatize leitura de arquivos CSV locais com script Python."
        )

        self.assertEqual(result["kind"], "automation-delegation")
        self.assertTrue(result["manual_only"])
        self.assertEqual(result["delegation"]["agent_id"], "python-automation-builder")
        self.assertIn("agent run python-automation-builder plan-python-automation", result["delegation"]["manual_command"])

    def test_playwright_delegation_contract_points_to_builder(self) -> None:
        result = self.repository.delegate_automation_build(
            request="Automatize um smoke test web com Playwright para validar formulario de login."
        )

        self.assertEqual(result["kind"], "automation-delegation")
        self.assertEqual(result["delegation"]["agent_id"], "playwright-automation-builder")
        self.assertEqual(result["delegation"]["capability_id"], "plan-playwright-automation")
        self.assertIn("agent run playwright-automation-builder plan-playwright-automation", result["delegation"]["manual_command"])

    def test_plan_without_request_returns_needs_input(self) -> None:
        result = self.repository.plan_automation_solution()

        self.assertEqual(result["status"], "needs-input")
        self.assertEqual(result["missing_fields"], ["request"])

    def test_generic_automation_prompt_routes_to_architect(self) -> None:
        plan = build_execution_plan(ROOT, "Automatize esta tarefa operacional escolhendo a melhor tecnologia.", dry_run=True)

        self.assertEqual(plan["routing_decision"]["selected_agent_id"], "automation-architect")
        self.assertEqual(plan["domain_agent"]["id"], "automation-architect")

    def test_classify_runner_is_executable_through_agent_cli(self) -> None:
        result = subprocess.run(
            [
                str(AGENT),
                "--json",
                "run",
                "automation-architect",
                "classify-automation-request",
                "--request",
                "Automatize coleta via API REST e gere JSON local.",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        runner_payload = json.loads(payload["stdout"])
        self.assertEqual(runner_payload["automation_type"], "python")
        self.assertEqual(runner_payload["recommended_agent"], "python-automation-builder")


if __name__ == "__main__":
    unittest.main()
