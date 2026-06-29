#!/usr/bin/env python3
"""Tests for the Technical Integration Analyst agent."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "ai-devkit"
AGENT = "technical-integration-analyst"
REQUIRED_CAPABILITIES = {
    "analyze-integration-flow",
    "extract-integration-contract",
    "generate-http-artifacts",
    "generate-protocol-artifacts",
    "generate-technical-docs",
    "generate-test-data",
    "identify-missing-information",
    "ingest-technical-docs",
    "run-integration-tests",
}


class TechnicalIntegrationAnalystCliTest(unittest.TestCase):
    def test_lists_required_capabilities(self) -> None:
        result = run_cli("--json", "capabilities", AGENT)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        capabilities = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertFalse(REQUIRED_CAPABILITIES - capabilities)

    def test_all_capabilities_have_runner(self) -> None:
        for capability in sorted(REQUIRED_CAPABILITIES):
            with self.subTest(capability=capability):
                result = run_cli("--json", "inspect", AGENT, capability)

                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                runner = payload["capability"]["entrypoint"]["runner"]
                self.assertTrue(runner["exists"])

    def test_extracts_contract_from_text_documentation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            doc = Path(tmpdir) / "api.md"
            doc.write_text(sample_http_documentation(), encoding="utf-8")

            result = run_cli("run", AGENT, "extract-integration-contract", "--file", str(doc))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Contrato de Integracao", result.stdout)
        self.assertIn("- Protocolo: rest", result.stdout)
        self.assertIn("POST /orders", result.stdout)
        self.assertIn("GET /orders/{orderId}", result.stdout)

    def test_generates_importable_postman_collection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            doc = Path(tmpdir) / "api.md"
            collection = Path(tmpdir) / "collection.json"
            doc.write_text(sample_http_documentation(), encoding="utf-8")

            result = run_cli(
                "run",
                AGENT,
                "generate-http-artifacts",
                "--file",
                str(doc),
                "--postman-output",
                str(collection),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(collection.read_text(encoding="utf-8"))

        self.assertEqual(payload["info"]["schema"], "https://schema.getpostman.com/json/collection/v2.1.0/collection.json")
        variables = {item["key"] for item in payload["variable"]}
        self.assertIn("base_url", variables)
        self.assertIn("token", variables)
        request_names = {item["name"] for item in payload["item"]}
        self.assertIn("POST /orders", request_names)
        self.assertIn("GET /orders/{orderId}", request_names)

    def test_run_integration_tests_defaults_to_dry_run_for_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            doc = Path(tmpdir) / "api.md"
            doc.write_text(sample_http_documentation(), encoding="utf-8")

            result = run_cli(
                "run",
                AGENT,
                "run-integration-tests",
                "--file",
                str(doc),
                "--base-url",
                "https://sandbox.example.test",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Plano de Testes de Integracao", result.stdout)
        self.assertIn("- Execucao real: False", result.stdout)
        self.assertIn("- POST /orders: dry-run", result.stdout)


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def sample_http_documentation() -> str:
    return """# Orders API

Base URL: https://sandbox.example.test
Authentication: Bearer token.

1. Create an order using POST /orders with JSON body {"customerId": "C123", "amount": 10.5}.
2. Read the order using GET /orders/{orderId}.
3. Cancel with DELETE /orders/{orderId}.

Errors: 400 validation_error, 401 unauthorized, 404 not_found.
"""


if __name__ == "__main__":
    unittest.main()
