#!/usr/bin/env python3
"""Agentic contract tests for N1 Support Agent."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "agents" / "n1-support-agent"


class N1SupportAgentContractTest(unittest.TestCase):
    def test_agent_loads_system_and_triage_contract_by_default(self) -> None:
        manifest = (AGENT / "agent.yaml").read_text(encoding="utf-8")

        self.assertIn("knowledge/system.md", manifest)
        self.assertIn(
            "knowledge/domains/customer-support/contracts/n1-support-triage-contract.json",
            manifest,
        )

    def test_no_future_cognito_agent_reference_remains(self) -> None:
        forbidden = "future-" + "cognito-analyzer"
        offenders = []
        for path in AGENT.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".md", ".yaml", ".json"}:
                if forbidden in path.read_text(encoding="utf-8"):
                    offenders.append(path.relative_to(ROOT).as_posix())

        self.assertEqual([], offenders)

    def test_core_auxiliary_capabilities_have_real_runners(self) -> None:
        capability_ids = [
            "extract-card-entities",
            "decide-n1-outcome",
            "generate-n1-artifacts",
            "update-azure-card",
            "analyze-cognito-user",
            "analyze-onboarding-status",
            "analyze-proposal-status",
            "collect-customer-logs",
        ]

        for capability_id in capability_ids:
            with self.subTest(capability=capability_id):
                runner = AGENT / "capabilities" / capability_id / "runner.py"
                source = runner.read_text(encoding="utf-8")
                self.assertNotIn("auxiliary_runner", source)
                self.assertNotIn("contract_ready", source)

    def test_stub_prompts_have_operational_contract(self) -> None:
        prompt_ids = [
            "extract-card-entities",
            "analyze-cognito-user",
            "analyze-onboarding-status",
            "analyze-proposal-status",
            "collect-customer-logs",
            "decide-n1-outcome",
            "generate-n1-artifacts",
            "update-azure-card",
        ]

        for prompt_id in prompt_ids:
            with self.subTest(prompt=prompt_id):
                prompt = AGENT / "knowledge" / "prompts" / f"{prompt_id}.md"
                text = prompt.read_text(encoding="utf-8")
                self.assertGreaterEqual(len(text.splitlines()), 20)
                self.assertIn("## Papel", text)
                self.assertIn("## Entradas", text)
                self.assertIn("## Saida", text)

    def test_updated_capability_manifests_expose_runner_inputs(self) -> None:
        expected_inputs = {
            "extract-card-entities": ["text", "fixture", "output", "format"],
            "analyze-cognito-user": ["cpf", "email", "phone", "fixture", "output", "format"],
            "analyze-onboarding-status": ["cpf", "proposal-number", "fixture", "output", "format"],
            "analyze-proposal-status": ["cpf", "proposal-number", "fixture", "output", "format"],
            "collect-customer-logs": ["cpf", "request-id", "correlation-id", "from-time", "to-time", "fixture", "output", "format"],
            "update-azure-card": ["project", "card", "tag", "target-state", "target-column", "current-state", "reason", "execute", "fixture", "output", "format"],
        }

        for capability_id, inputs in expected_inputs.items():
            with self.subTest(capability=capability_id):
                manifest = (AGENT / "capabilities" / capability_id / "capability.yaml").read_text(encoding="utf-8")
                for input_name in inputs:
                    self.assertIn(input_name, manifest)


if __name__ == "__main__":
    unittest.main()
