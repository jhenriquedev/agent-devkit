#!/usr/bin/env python3
"""Agentic contract tests for the Elasticsearch Log Analyzer package."""

from __future__ import annotations

import unittest
from pathlib import Path


AGENT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (AGENT / relative_path).read_text(encoding="utf-8")


class ElasticsearchAgenticContractsTest(unittest.TestCase):
    def test_decision_rules_document_scope_limits_and_sensitive_payload_boundaries(self) -> None:
        expected_markers = {
            "list-log-sources": ["runtime", ".env", "limit"],
            "search-log-events": ["source", "janela", "limit", "authorization"],
            "trace-request": ["source", "janela", "limit", "identificador"],
            "extract-log-samples": ["bounded", "segredo", "api key", "authorization"],
            "analyze-service-errors": ["source", "janela", "limit", "inferencia"],
            "detect-error-patterns": ["heuristica", "amostra", "causa-raiz"],
            "generate-log-report": ["source", "janela", "limit", "fato", "inferencia"],
            "correlate-azure-card-logs": ["card", "contexto", "evidencia", "conservadora"],
        }

        for capability_id, markers in expected_markers.items():
            with self.subTest(capability=capability_id):
                rules = read(f"capabilities/{capability_id}/decision-rules.md").lower()
                for marker in markers:
                    self.assertIn(marker, rules)

    def test_sample_prompt_does_not_allow_secret_exposure_by_default(self) -> None:
        prompt = read("knowledge/prompts/extract-log-samples.md").lower()

        self.assertIn("não copiar segredos", prompt)
        self.assertIn("sinalize sem reproduzir", prompt)
        self.assertNotIn("não redija/oculte campos por default", prompt)


if __name__ == "__main__":
    unittest.main()
