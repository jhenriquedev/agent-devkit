#!/usr/bin/env python3
"""Agentic contract tests for the BPO Analyser package."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "agents" / "bpo-analyser"


def read(relative_path: str) -> str:
    return (AGENT / relative_path).read_text(encoding="utf-8")


class BpoAgenticContractsTest(unittest.TestCase):
    def test_default_context_loads_system_and_domain_glossary(self) -> None:
        manifest = read("agent.yaml")
        system_prompt = read("knowledge/system.md")
        glossary = read("knowledge/domain-glossary.md")

        self.assertIn(
            "default_context:\n  - knowledge/system.md\n  - knowledge/context.md\n"
            "  - knowledge/policies.yaml\n  - knowledge/domain-glossary.md",
            manifest,
        )
        self.assertIn("BPO Analyser", system_prompt)
        self.assertIn("read-only", system_prompt)
        self.assertIn("BPO_FORBIDDEN_URL_PATTERNS", system_prompt)
        self.assertIn("Fatos", system_prompt)
        self.assertIn("Inferencias", system_prompt)
        self.assertIn("ArquivoBase64", system_prompt)
        self.assertIn("INT", glossary)
        self.assertIn("APR", glossary)
        self.assertIn("BPO_ELIGIBLE_PROPOSAL_TYPES", glossary)
        self.assertIn("limiteSaque > 0", glossary)
        self.assertIn("metadados", glossary)

    def test_prompts_have_capability_specific_decision_rules(self) -> None:
        expected_markers = {
            "test-connection": [
                "BPO_SERVICO_API_URL",
                "BPO_CARTAO_PASSWORD",
                "WSDL",
                "nao imprima valores",
            ],
            "consult-proposal": [
                "processing_status.status == false",
                "motivoReprovacao",
                "CPF mascarado",
                "payload SOAP",
            ],
            "consult-attached-documents": [
                "metadados",
                "ArquivoBase64",
                "--include-content",
                "nao interprete o conteudo",
            ],
            "analyze-proposal": [
                "has_blocking_signals",
                "sem documentos",
                "possivel pendencia de formalizacao",
                "nao sugira mutacao",
            ],
            "list-proposals-by-cpf": [
                "Normalize o CPF",
                "CPF mascarado",
                "is_eligible",
                "BPO_FORBIDDEN_URL_PATTERNS",
            ],
            "analyze-cpf-proposals": [
                "elegiveis",
                "em analise",
                "reprovadas",
                "politica operacional",
            ],
            "find-latest-proposal-by-cpf": [
                "INT",
                "APR",
                "last_due_date",
                "sem selecao",
            ],
        }

        for prompt_id, markers in expected_markers.items():
            with self.subTest(prompt=prompt_id):
                prompt = read(f"knowledge/prompts/{prompt_id}.md")
                self.assertIn("## Objetivo", prompt)
                self.assertIn("## Entradas", prompt)
                self.assertIn("## Raciocinio", prompt)
                self.assertIn("## Decisao", prompt)
                self.assertIn("## Saida", prompt)
                self.assertIn("## Nao faca", prompt)
                normalized = prompt.lower()
                for marker in markers:
                    self.assertIn(marker.lower(), normalized)

    def test_policies_and_templates_document_runtime_contract(self) -> None:
        policies = read("knowledge/policies.yaml")
        knowledge_readme = read("knowledge/README.md")

        self.assertIn("decision_policy", policies)
        self.assertIn("prefer_proposal_number", policies)
        self.assertIn("processing_status_false", policies)
        self.assertIn("missing_documents", policies)
        self.assertIn("human_escalation", policies)
        self.assertIn("domain-glossary.md", knowledge_readme)
        self.assertIn("diagnostico", knowledge_readme)

        for template_path in (AGENT / "templates").glob("*-output.md"):
            with self.subTest(template=template_path.name):
                template = template_path.read_text(encoding="utf-8")
                self.assertIn("##", template)
                self.assertRegex(template, r"Fatos|Diagnostico|Resultado")
                if template_path.name != "test-connection-output.md":
                    self.assertIn("CPF", template)
                if "document" in template_path.name or "proposal" in template_path.name:
                    self.assertIn("base64", template.lower())

    def test_decision_rules_document_sensitive_data_boundaries(self) -> None:
        expected_markers = {
            "test-connection": ["credenciais", "--network", "configuracao local"],
            "list-proposals-by-cpf": ["cpf", "mascarado", "bpo_forbidden_url_patterns", "payload soap"],
            "analyze-cpf-proposals": ["cpf", "mascarado", "bpo_forbidden_url_patterns", "payload soap"],
            "find-latest-proposal-by-cpf": ["cpf", "mascarado", "bpo_forbidden_url_patterns", "payload soap"],
            "consult-proposal": [
                "cpf",
                "mascarado",
                "bpo_forbidden_url_patterns",
                "payload soap",
                "fatos",
                "inferencias",
            ],
            "consult-attached-documents": [
                "arquivobase64",
                "--include-content",
                "bpo_forbidden_url_patterns",
                "conteudo binario",
            ],
            "analyze-proposal": [
                "bpo_forbidden_url_patterns",
                "base64",
                "fatos",
                "inferencias",
                "mutacao",
            ],
        }

        for capability_id, markers in expected_markers.items():
            with self.subTest(capability=capability_id):
                rules = read(f"capabilities/{capability_id}/decision-rules.md").lower()
                for marker in markers:
                    self.assertIn(marker, rules)

    def test_agent_has_no_project_specific_references(self) -> None:
        forbidden_markers = [
            "meu" + "cash",
            "m" + "cc",
            "self" + "hire",
            "self" + "-hire",
            "regra do " + "co" + "re",
            "/api/v1/self" + "-hire",
        ]
        for path in AGENT.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or "tests" in path.parts:
                continue
            content = path.read_text(encoding="utf-8", errors="ignore").lower()
            for marker in forbidden_markers:
                with self.subTest(path=path.relative_to(AGENT), marker=marker):
                    self.assertNotIn(marker, content)


if __name__ == "__main__":
    unittest.main()
