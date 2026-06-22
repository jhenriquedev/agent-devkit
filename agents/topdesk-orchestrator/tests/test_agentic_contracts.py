#!/usr/bin/env python3
"""Agentic contract tests for TOPdesk Orchestrator."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "agents" / "topdesk-orchestrator"


class TopdeskAgenticContractTest(unittest.TestCase):
    def test_agent_loads_system_prompt_and_triage_rules(self) -> None:
        manifest = (AGENT / "agent.yaml").read_text(encoding="utf-8")

        default_context_index = manifest.index("default_context:")
        first_context_index = manifest.index("  - ", default_context_index)
        first_context_line = manifest[first_context_index:].splitlines()[0]
        self.assertEqual(first_context_line, "  - knowledge/system.md")
        self.assertIn("  - knowledge/triage-rules.md", manifest)
        self.assertTrue((AGENT / "knowledge" / "system.md").exists())
        self.assertTrue((AGENT / "knowledge" / "triage-rules.md").exists())

    def test_prompts_are_not_placeholders(self) -> None:
        for prompt in sorted((AGENT / "knowledge" / "prompts").glob("*.md")):
            if prompt.name == "README.md":
                continue
            with self.subTest(prompt=prompt.name):
                text = prompt.read_text(encoding="utf-8")
                self.assertGreaterEqual(len(text.splitlines()), 18)
                for section in ("## Objetivo", "## Entradas", "## Raciocinio", "## Saida", "## Nao faca"):
                    self.assertIn(section, text)

    def test_templates_document_facts_and_inferences_contract(self) -> None:
        for template in sorted((AGENT / "templates").glob("*-output.md")):
            with self.subTest(template=template.name):
                text = template.read_text(encoding="utf-8")
                self.assertIn("## Fatos (TOPdesk)", text)
                self.assertIn("## Inferencias (agente)", text)
                self.assertIn("## Proxima acao", text)

    def test_decision_rules_are_capability_specific(self) -> None:
        contents = {}
        for rules in sorted((AGENT / "capabilities").glob("*/decision-rules.md")):
            with self.subTest(rules=rules.parent.name):
                text = rules.read_text(encoding="utf-8")
                self.assertGreaterEqual(len(text.splitlines()), 8)
                self.assertIn(rules.parent.name, text)
                contents[rules.parent.name] = text
        self.assertGreater(len(set(contents.values())), 1)

    def test_triage_incident_is_declared_and_uses_orphan_methods(self) -> None:
        manifest = (AGENT / "agent.yaml").read_text(encoding="utf-8")
        capability = AGENT / "capabilities" / "triage-incident" / "capability.yaml"
        text = capability.read_text(encoding="utf-8")

        self.assertIn("  - triage-incident", manifest)
        self.assertIn("get-catalog.yaml", text)
        self.assertIn("search-persons.yaml", text)


if __name__ == "__main__":
    unittest.main()
