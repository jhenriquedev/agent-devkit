#!/usr/bin/env python3
"""Tests for the knowledge-generator agent runners."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


class KnowledgeGeneratorRunnersTest(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def parse_runner_payload(self, result: subprocess.CompletedProcess[str]) -> dict:
        payload = json.loads(result.stdout)
        if "stdout" in payload:
            return json.loads(payload["stdout"])
        return payload

    def write_sample_source(self, root: Path) -> None:
        (root / "README.md").write_text("# Sample\n\nDocumento de suporte.\n", encoding="utf-8")
        (root / "app.py").write_text(
            "import os\n\n"
            "class CustomerService:\n"
            "    def find_customer(self, cpf):\n"
            "        print('correlation_id', cpf)\n"
            "        return os.environ.get('CUSTOMER_API_URL')\n",
            encoding="utf-8",
        )
        (root / "api.ts").write_text(
            "export class ApiClient {\n"
            "  async getCustomer(id: string) { return fetch(`/customers/${id}`); }\n"
            "}\n",
            encoding="utf-8",
        )
        (root / "Program.cs").write_text(
            "public class Program { public static void Main(string[] args) {} }\n",
            encoding="utf-8",
        )
        (root / "main.dart").write_text(
            "import 'package:flutter/widgets.dart';\n"
            "class HomePage extends StatelessWidget { Widget build(context) => Text('Home'); }\n",
            encoding="utf-8",
        )
        (root / "index.html").write_text(
            "<html><body><form action=\"/login\"><input id=\"cpf\"></form></body></html>",
            encoding="utf-8",
        )
        (root / "styles.css").write_text(
            ":root { --brand: #123456; } @media (max-width: 600px) { body { margin: 0; } }",
            encoding="utf-8",
        )
        (root / "notes.json").write_text('{"decision": "usar adapter flexivel"}', encoding="utf-8")

    def test_list_profiles_reports_supported_profiles(self) -> None:
        result = self.run_cli("--json", "run", "knowledge-generator", "list-knowledge-profiles")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_runner_payload(result)
        profile_ids = {item["id"] for item in payload["profiles"]}
        self.assertIn("code-project", profile_ids)
        self.assertIn("documentation-set", profile_ids)
        self.assertIn("frontend-app", profile_ids)
        self.assertIn("mixed-knowledge", profile_ids)

    def test_inspect_source_detects_common_code_and_document_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            source.mkdir()
            self.write_sample_source(source)

            result = self.run_cli(
                "--json",
                "run",
                "knowledge-generator",
                "inspect-source",
                "--source",
                str(source),
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_runner_payload(result)
        self.assertEqual(payload["recommended_profile"], "code-project")
        languages = set(payload["source"]["languages"])
        self.assertGreaterEqual(
            languages,
            {"python", "typescript", "csharp", "dart", "html", "css"},
        )
        self.assertIn("documentation", payload["source"]["content_kinds"])

    def test_generate_knowledge_creates_profile_specific_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            output = Path(tmpdir) / "knowledge"
            source.mkdir()
            self.write_sample_source(source)

            result = self.run_cli(
                "run",
                "knowledge-generator",
                "generate-knowledge",
                "--source",
                str(source),
                "--project-id",
                "sample-app",
                "--profile",
                "auto",
                "--output-dir",
                str(output),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "project.json").exists())
            self.assertTrue((output / "source-index.json").exists())
            self.assertTrue((output / "code-inventory.json").exists())
            self.assertTrue((output / "coverage-assessment.md").exists())
            self.assertTrue((output / "hardening" / "initial-gaps.json").exists())

            project = json.loads((output / "project.json").read_text(encoding="utf-8"))
            inventory = json.loads((output / "code-inventory.json").read_text(encoding="utf-8"))

        self.assertEqual(project["project"]["id"], "sample-app")
        self.assertEqual(project["profile"], "code-project")
        self.assertIn("dart", inventory["languages"])
        self.assertIn("html", inventory["languages"])
        self.assertIn("css", inventory["languages"])
        symbols = {symbol["name"] for symbol in inventory["symbols"]}
        self.assertIn("CustomerService", symbols)
        self.assertIn("HomePage", symbols)

    def test_validate_knowledge_accepts_generated_knowledge(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            output = Path(tmpdir) / "knowledge"
            source.mkdir()
            self.write_sample_source(source)

            generate = self.run_cli(
                "run",
                "knowledge-generator",
                "generate-knowledge",
                "--source",
                str(source),
                "--project-id",
                "sample-app",
                "--output-dir",
                str(output),
                "--yes-create-dir",
            )
            self.assertEqual(generate.returncode, 0, generate.stderr)

            validate = self.run_cli(
                "--json",
                "run",
                "knowledge-generator",
                "validate-knowledge",
                "--knowledge-dir",
                str(output),
            )

        self.assertEqual(validate.returncode, 0, validate.stderr)
        payload = self.parse_runner_payload(validate)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["errors"], [])


if __name__ == "__main__":
    unittest.main()
