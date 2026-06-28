#!/usr/bin/env python3
"""Agentic contract tests for the Azure DevOps Orchestrator package."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "agents" / "azure-devops-orchestrator"
CLI = ROOT / "ai-devkit"


def read(relative_path: str) -> str:
    return (AGENT / relative_path).read_text(encoding="utf-8")


class AzureDevOpsAgenticContractsTest(unittest.TestCase):
    def test_default_context_loads_system_prompt_first(self) -> None:
        manifest = read("agent.yaml")
        system_prompt = read("knowledge/system.md")

        self.assertIn("default_context:\n  - knowledge/system.md", manifest)
        self.assertIn("Azure DevOps Orchestrator", system_prompt)
        self.assertIn("FATO", system_prompt)
        self.assertIn("INFERENCIA", system_prompt)
        self.assertIn("confirmacao explicita", system_prompt)
        self.assertIn("--execute", system_prompt)
        self.assertIn("System.BoardColumn", system_prompt)
        self.assertIn("email ou unique_name", system_prompt)

    def test_attach_file_is_official_capability_with_method_contract(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "azure-devops-orchestrator",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        capability_ids = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertIn("attach-file", capability_ids)

        manifest = read("agent.yaml")
        capability = read("capabilities/attach-file/capability.yaml")
        method = read("infra/integrations/azure/methods/attach-file.yaml")
        rules = read("capabilities/attach-file/decision-rules.md")
        template = read("templates/attach-file-output.md")

        self.assertIn("- attach-file", manifest)
        self.assertIn("infra/integrations/azure/methods/attach-file.yaml", manifest)
        self.assertIn("methods/attach-file.yaml", capability)
        self.assertIn("repository_method: attach_file", method)
        self.assertIn("confirmation_required: true", method)
        self.assertIn("arquivo existe", rules)
        self.assertIn("Target", template)
        self.assertIn("Confirmation", template)

    def test_policies_only_advertise_supported_repository_operations(self) -> None:
        policies = read("knowledge/policies.yaml")

        self.assertIn("- list_work_items", policies)
        self.assertIn("- get_work_item", policies)
        self.assertIn("- get_work_item_comments", policies)
        self.assertIn("- find_users", policies)
        self.assertIn("- attach_file", policies)
        self.assertNotIn("- list_projects", policies)
        self.assertNotIn("- list_boards", policies)
        self.assertNotIn("- list_queries", policies)
        self.assertIn("host_guidance", policies)

    def test_write_capabilities_document_confirmation_boundary(self) -> None:
        for capability_id in (
            "assign-card",
            "attach-file",
            "comment-card",
            "move-card",
            "update-card-tags",
        ):
            with self.subTest(capability=capability_id):
                capability = read(f"capabilities/{capability_id}/capability.yaml")
                rules = read(f"capabilities/{capability_id}/decision-rules.md").lower()

                self.assertIn("write_policy: confirm", capability)
                self.assertIn("confirmacao", rules)
                self.assertTrue(
                    "dry-run" in rules or "--execute" in rules,
                    f"{capability_id} must document dry-run or --execute behavior",
                )

    def test_prompts_preserve_domain_specific_decision_rules(self) -> None:
        expected_markers = {
            "list-cards": [
                "WIQL",
                "limite",
                "nenhuma escrita",
                "nao infira prioridade",
            ],
            "read-card": [
                "Fatos",
                "Inferencias",
                "criterio de aceite",
                "logs sensiveis",
            ],
            "comment-card": [
                "preview",
                "add-comment",
                "--execute",
                "dados sensiveis",
            ],
            "update-card-tags": [
                "Preserve tags existentes",
                "remova apenas",
                "no-op",
                "JSON patch",
            ],
            "assign-card": [
                "email ou unique_name",
                "multiplos candidatos",
                "skip_identity_lookup",
                "endpoint de identidade varia por tenant",
            ],
            "move-card": [
                "Fechamento exige reason",
                "System.BoardColumn",
                "nao altere tags ou responsavel",
                "no-op",
            ],
            "prepare-card-analysis": [
                "fatos",
                "hipoteses",
                "comment-card",
                "sem escrita",
            ],
            "generate-cards-report": [
                "read-only",
                "sem responsavel",
                "sem criterio de aceite",
                "possivel truncamento",
            ],
            "attach-file": [
                "arquivo existe localmente",
                "--execute",
                "AttachedFile",
                "dados sensiveis",
            ],
        }

        for prompt_id, markers in expected_markers.items():
            with self.subTest(prompt=prompt_id):
                prompt = read(f"knowledge/prompts/{prompt_id}.md")
                self.assertIn("Objetivo:", prompt)
                self.assertIn("Entradas esperadas:", prompt)
                self.assertIn("Passos de raciocinio:", prompt)
                self.assertIn("Regras de decisao:", prompt)
                self.assertIn("NAO faca:", prompt)
                normalized = prompt.lower()
                for marker in markers:
                    self.assertIn(marker.lower(), normalized)


if __name__ == "__main__":
    unittest.main()
