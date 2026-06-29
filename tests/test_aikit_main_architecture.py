#!/usr/bin/env python3
"""Architectural contracts for the thin public CLI entrypoint."""

from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "cli" / "aikit" / "main.py"
CLI_TIMEOUT_SECONDS = 60


class AikitMainArchitectureTest(unittest.TestCase):
    def test_main_entrypoint_stays_thin(self) -> None:
        tree = ast.parse(MAIN_PATH.read_text(encoding="utf-8"))
        functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}

        self.assertEqual(functions, {"main"})
        self.assertEqual(classes, set())

    def test_main_does_not_reintroduce_runtime_responsibilities(self) -> None:
        text = MAIN_PATH.read_text(encoding="utf-8")
        forbidden = (
            "def print_",
            "def dispatch_",
            "def agent_requires_llm",
            "def run_capability",
            "def list_agents",
            "def load_agent",
            "def doctor",
            "def run_interactive_wizard",
            "class DevKitError",
        )
        for marker in forbidden:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, text)

    def test_extracted_runtime_modules_are_importable(self) -> None:
        modules = (
            "cli.aikit.cli_parser",
            "cli.aikit.cli_dispatch",
            "cli.aikit.core.requests",
            "cli.aikit.core.runtime",
            "cli.aikit.natural_prompt_runtime",
            "cli.aikit.capability_runtime",
            "cli.aikit.doctor_runtime",
            "cli.aikit.interactive_wizard",
            "cli.aikit.human_output",
        )
        for module in modules:
            with self.subTest(module=module):
                __import__(module)

    def test_public_cli_contract_still_works(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "agent"), "--version"],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CLI_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("agent ", result.stdout)

    def test_architecture_contract_exposes_agent_devkit_as_principal_agent(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "agent"), "--json", "architecture"],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CLI_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        import json

        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "architecture")
        self.assertEqual(payload["schema_version"], "ai-devkit.architecture/v1")
        self.assertEqual(payload["principal_agent"]["name"], "Agent DevKit")
        self.assertEqual(payload["model"]["agents"], "modulos especialistas internos versionados em agents/*")
        self.assertIn("deterministic_capability", payload["decision_targets"])
        self.assertIn("external_host_via_mcp", payload["decision_targets"])
        self.assertEqual(payload["recommended_initial_order"], [1, 2, 3, 4, 7, 8, 6, 5, 36])
        phases = {item["number"]: item for item in payload["implementation_phases"]}
        self.assertEqual(phases[0]["name"], "Decisao Arquitetural")
        self.assertIn(1, phases[0]["problems"])
        self.assertIn(2, phases[1]["problems"])
        self.assertIn(3, phases[1]["problems"])
        self.assertIn(4, phases[1]["problems"])
        self.assertIn(6, phases[1]["problems"])
        self.assertIn(7, phases[2]["problems"])
        self.assertIn(8, phases[2]["problems"])
        self.assertIn(9, phases[2]["problems"])
        self.assertIn(11, phases[2]["problems"])
        self.assertIn(12, phases[2]["problems"])
        self.assertIn(36, phases[4]["problems"])
        acceptance = payload["acceptance_model"]
        section_ids = {section["id"] for section in acceptance["sections"]}
        self.assertGreaterEqual(
            section_ids,
            {
                "contract",
                "behavior",
                "security",
                "compatibility",
                "validation",
                "out_of_scope",
            },
        )
        change_type_ids = {change_type["id"] for change_type in acceptance["change_types"]}
        self.assertGreaterEqual(
            change_type_ids,
            {
                "agent",
                "capability",
                "runner",
                "integration",
                "host_plugin",
                "core_change",
            },
        )
        self.assertTrue(acceptance["definition_of_done"])
        impact = payload["impact_model"]
        area_ids = {area["id"] for area in impact["areas"]}
        self.assertGreaterEqual(
            area_ids,
            {
                "cli",
                "core_execution",
                "registry",
                "policies_guardrails",
                "providers_sources",
                "audit",
                "mcp",
                "validation_gates",
                "agents_capabilities",
            },
        )
        self.assertTrue(impact["spec_template"])

    def test_implementation_phase_contract_is_complete_and_indexed(self) -> None:
        from cli.aikit.roadmap import implementation_phases, problem_phase_map, recommended_initial_order

        phases = implementation_phases()
        phase_ids = {phase["id"] for phase in phases}
        mapping = problem_phase_map()

        self.assertEqual(recommended_initial_order(), [1, 2, 3, 4, 7, 8, 6, 5, 36])
        self.assertEqual(len(phases), 10)
        self.assertEqual({phase["number"] for phase in phases}, set(range(10)))
        for phase in phases:
            self.assertIn(phase["id"], phase_ids)
            self.assertTrue(phase["goal"])
            self.assertTrue(phase["deliverables"])
            self.assertTrue(phase["exit_conditions"])
            for problem in phase["problems"]:
                self.assertEqual(mapping[problem]["phase_id"], phase["id"])
                self.assertEqual(mapping[problem]["phase_number"], phase["number"])

    def test_acceptance_model_contract_is_complete(self) -> None:
        from cli.aikit.acceptance import acceptance_model, acceptance_sections, change_type_acceptance

        model = acceptance_model()
        section_ids = {section["id"] for section in model["sections"]}
        change_type_ids = {change_type["id"] for change_type in model["change_types"]}
        expected_sections = {
            "contract",
            "behavior",
            "security",
            "compatibility",
            "validation",
            "out_of_scope",
        }
        expected_change_types = {
            "agent",
            "capability",
            "runner",
            "integration",
            "host_plugin",
            "core_change",
        }

        self.assertEqual(section_ids, set(acceptance_sections()))
        self.assertGreaterEqual(section_ids, expected_sections)
        self.assertEqual(change_type_ids, set(change_type_acceptance()))
        self.assertGreaterEqual(change_type_ids, expected_change_types)
        for change_type in model["change_types"]:
            self.assertTrue(change_type["criteria"], change_type["id"])
        self.assertTrue(model["global_criteria"])
        self.assertTrue(model["definition_of_done"])

    def test_impact_model_contract_is_complete(self) -> None:
        from cli.aikit.impact_map import ownership_area_ids, ownership_model, spec_impact_template

        model = ownership_model()
        area_ids = {area["id"] for area in model["areas"]}
        expected_areas = {
            "cli",
            "core_execution",
            "registry",
            "policies_guardrails",
            "providers_sources",
            "llm_mini_brain",
            "sessions_memory_tasks_scheduler",
            "audit",
            "mcp",
            "validation_gates",
            "agents_capabilities",
        }

        self.assertEqual(area_ids, set(ownership_area_ids()))
        self.assertGreaterEqual(area_ids, expected_areas)
        for area in model["areas"]:
            self.assertTrue(area["paths"], area["id"])
            self.assertTrue(area["responsibilities"], area["id"])
            self.assertIn("should_not_contain", area)
        self.assertEqual(model["spec_template"], spec_impact_template())
        self.assertIn("likely_files", model["spec_template"])
        self.assertIn("boundary_crossing_justification", model["spec_template"])

    def test_pull_request_template_references_acceptance_model(self) -> None:
        text = (ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")

        self.assertIn("Criterios de aceite", text)
        self.assertIn("Mapa de impacto", text)
        self.assertIn("Arquivos provaveis", text)
        self.assertIn("Contratos afetados", text)
        self.assertIn("Gates relacionados", text)
        self.assertIn("Testes executados", text)
        self.assertIn("Fora de escopo", text)
        self.assertIn("agent architecture --json", text)


if __name__ == "__main__":
    unittest.main()
