#!/usr/bin/env python3
"""Agentic contract tests for N2 Support Agent."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "agents" / "n2-support-agent"


class N2SupportAgentContractTest(unittest.TestCase):
    def test_agent_loads_system_prompt_first_and_declares_real_azure_actions(self) -> None:
        manifest = (AGENT / "agent.yaml").read_text(encoding="utf-8")

        default_context_index = manifest.index("default_context:")
        first_context_index = manifest.index("  - ", default_context_index)
        first_context_line = manifest[first_context_index:].splitlines()[0]
        self.assertEqual(first_context_line, "  - knowledge/system.md")
        self.assertIn("azure-devops-orchestrator/assign-card", manifest)
        for future_or_unused_agent in ("topdesk-orchestrator", "database-change-operator", "sqlserver-change-operator"):
            self.assertNotIn(future_or_unused_agent, manifest)

    def test_all_prompts_have_agentic_operational_structure(self) -> None:
        for prompt in sorted((AGENT / "knowledge" / "prompts").glob("*.md")):
            if prompt.name == "README.md":
                continue
            with self.subTest(prompt=prompt.name):
                text = prompt.read_text(encoding="utf-8")
                self.assertGreaterEqual(len(text.splitlines()), 20)
                for section in ("## Objetivo", "## Entradas", "## Raciocinio", "## Saida", "## Nao faca"):
                    self.assertIn(section, text)

    def test_short_workflows_document_deterministic_steps(self) -> None:
        workflow_ids = [
            "analyze-code-root-cause",
            "build-reproduction-strategy",
            "classify-root-cause",
            "correlate-runtime-evidence",
            "generate-card-comment",
            "load-support-context",
            "rank-code-findings",
            "review-patch-plan-readiness",
            "select-specialist-checks",
            "validate-n1-handoff",
        ]

        for workflow_id in workflow_ids:
            with self.subTest(workflow=workflow_id):
                workflow = AGENT / "capabilities" / workflow_id / "workflow.md"
                text = workflow.read_text(encoding="utf-8")
                self.assertGreaterEqual(len(text.splitlines()), 12)
                self.assertIn("## Fluxo", text)

    def test_taxonomy_and_validation_catalog_are_versioned_knowledge(self) -> None:
        taxonomy = AGENT / "knowledge" / "runbooks" / "root-cause-taxonomy.md"
        catalog = AGENT / "knowledge" / "runbooks" / "specialist-validation-catalog.md"

        self.assertTrue(taxonomy.exists())
        self.assertTrue(catalog.exists())
        self.assertIn("backend_bug", taxonomy.read_text(encoding="utf-8"))
        self.assertIn("elasticsearch-log-analyzer", catalog.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
