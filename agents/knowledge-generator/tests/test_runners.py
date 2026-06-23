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


class KnowledgeGeneratorSecretMaskingTest(unittest.TestCase):
    """Unit tests for secret masking — do not require the CLI."""

    def _repo(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "infra" / "integrations" / "local-source"))
        from knowledge_repository import mask_secrets  # type: ignore
        return mask_secrets

    def test_masks_bearer_token(self) -> None:
        mask = self._repo()
        result = mask("Authorization: Bearer supersecrettoken123")
        self.assertNotIn("supersecrettoken123", result)
        self.assertIn("{{token}}", result)

    def test_masks_api_key(self) -> None:
        mask = self._repo()
        result = mask("api_key=abc123xyz")
        self.assertNotIn("abc123xyz", result)
        self.assertIn("{{api_key}}", result)

    def test_masks_password(self) -> None:
        mask = self._repo()
        result = mask("password=hunter2")
        self.assertNotIn("hunter2", result)
        self.assertIn("{{password}}", result)

    def test_masks_connection_string(self) -> None:
        mask = self._repo()
        result = mask("connection_string=Server=myserver;User=sa;Password=secret123")
        self.assertNotIn("secret123", result)

    def test_masks_private_key_pem_block(self) -> None:
        mask = self._repo()
        pem = (
            "-----BEGIN PRIVATE KEY-----\n"
            "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7\n"
            "-----END PRIVATE KEY-----"
        )
        result = mask(pem)
        self.assertNotIn("MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7", result)
        self.assertIn("{{private_key}}", result)

    def test_masks_certificate_pem_block(self) -> None:
        mask = self._repo()
        cert = (
            "-----BEGIN CERTIFICATE-----\n"
            "MIIDXTCCAkWgAwIBAgIJAJC1HiIAZAiIMA0GCSqGSIb3DQEBCwUA\n"
            "-----END CERTIFICATE-----"
        )
        result = mask(cert)
        self.assertNotIn("MIIDXTCCAkWgAwIBAgIJAJC1HiIAZAiIMA0GCSqGSIb3DQEBCwUA", result)
        self.assertIn("{{certificate}}", result)

    def test_masks_cookie_header(self) -> None:
        mask = self._repo()
        result = mask("set-cookie: session=abc123xyz; HttpOnly")
        self.assertNotIn("abc123xyz", result)


class KnowledgeGeneratorProfilesTest(unittest.TestCase):
    """Tests for the additional profiles beyond code-project."""

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

    def _generate(self, source: Path, output: Path, profile: str, project_id: str) -> subprocess.CompletedProcess[str]:
        return self.run_cli(
            "run",
            "knowledge-generator",
            "generate-knowledge",
            "--source", str(source),
            "--profile", profile,
            "--project-id", project_id,
            "--output-dir", str(output),
            "--yes-create-dir",
        )

    def _write_domain_source(self, root: Path) -> None:
        (root / "policy.md").write_text(
            "# Regra de negocio\n\nO cliente deve fornecer CPF para abertura de conta.\n"
            "Processo de validacao: verificar ator no sistema de cadastro.\n",
            encoding="utf-8",
        )

    def _write_integration_source(self, root: Path) -> None:
        (root / "api.md").write_text(
            "# Endpoint GET /customers\n\nAuth: Bearer token.\n"
            "Payload: {id, name}. Errors: 404 not found.\n",
            encoding="utf-8",
        )

    def _write_operations_source(self, root: Path) -> None:
        (root / "runbook.md").write_text(
            "# Runbook: Incident de login\n\nSintoma: usuario nao consegue logar.\n"
            "Troubleshooting: verificar playbook de autenticacao.\n",
            encoding="utf-8",
        )

    def _write_documentation_source(self, root: Path) -> None:
        (root / "manual.md").write_text("# Manual\n\nDocumento de referencia.\n", encoding="utf-8")
        (root / "guide.txt").write_text("Guia de uso.", encoding="utf-8")

    def _write_data_source(self, root: Path) -> None:
        (root / "schema.json").write_text('{"table": "customers", "columns": ["id", "name"]}', encoding="utf-8")
        (root / "data.csv").write_text("id,name\n1,Alice\n2,Bob\n", encoding="utf-8")

    def _write_freeform_source(self, root: Path) -> None:
        (root / "note.txt").write_text("Anotacao livre sem estrutura.", encoding="utf-8")

    def test_business_domain_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            output = Path(tmpdir) / "knowledge"
            source.mkdir()
            self._write_domain_source(source)
            result = self._generate(source, output, "business-domain", "biz-test")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "domain.json").exists())
            data = json.loads((output / "domain.json").read_text(encoding="utf-8"))
            self.assertIn("items", data)
            self.assertIsInstance(data["items"], list)
            # Items should have required fields
            for item in data["items"]:
                self.assertIn("id", item)
                self.assertIn("type", item)
                self.assertIn("status", item)

    def test_integration_docs_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            output = Path(tmpdir) / "knowledge"
            source.mkdir()
            self._write_integration_source(source)
            result = self._generate(source, output, "integration-docs", "int-test")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "integration.json").exists())
            data = json.loads((output / "integration.json").read_text(encoding="utf-8"))
            self.assertIn("items", data)

    def test_support_operations_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            output = Path(tmpdir) / "knowledge"
            source.mkdir()
            self._write_operations_source(source)
            result = self._generate(source, output, "support-operations", "ops-test")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "operations.json").exists())
            data = json.loads((output / "operations.json").read_text(encoding="utf-8"))
            self.assertIn("items", data)

    def test_documentation_set_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            output = Path(tmpdir) / "knowledge"
            source.mkdir()
            self._write_documentation_source(source)
            result = self._generate(source, output, "documentation-set", "docs-test")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "document-map.json").exists())

    def test_data_domain_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            output = Path(tmpdir) / "knowledge"
            source.mkdir()
            self._write_data_source(source)
            result = self._generate(source, output, "data-domain", "data-test")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "data-inventory.json").exists())

    def test_freeform_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            output = Path(tmpdir) / "knowledge"
            source.mkdir()
            self._write_freeform_source(source)
            result = self._generate(source, output, "freeform", "ff-test")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "project.json").exists())

    def test_mixed_knowledge_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            output = Path(tmpdir) / "knowledge"
            source.mkdir()
            self._write_documentation_source(source)
            self._write_data_source(source)
            result = self._generate(source, output, "mixed-knowledge", "mixed-test")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "project.json").exists())

    def test_frontend_app_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            output = Path(tmpdir) / "knowledge"
            source.mkdir()
            (source / "app.ts").write_text("export class App { render() { return '<div>hello</div>'; } }", encoding="utf-8")
            (source / "style.css").write_text(":root { --primary: #fff; }", encoding="utf-8")
            result = self._generate(source, output, "frontend-app", "fe-test")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "frontend-inventory.json").exists())


class KnowledgeGeneratorOverwriteTest(unittest.TestCase):
    """Tests for the overwrite and directory-creation guardrails."""

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_generate_fails_without_yes_create_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            output = Path(tmpdir) / "nonexistent"
            source.mkdir()
            (source / "file.txt").write_text("hello", encoding="utf-8")

            result = self.run_cli(
                "run",
                "knowledge-generator",
                "generate-knowledge",
                "--source", str(source),
                "--output-dir", str(output),
            )
        self.assertNotEqual(result.returncode, 0)

    def test_generate_fails_on_overwrite_without_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            output = Path(tmpdir) / "knowledge"
            source.mkdir()
            (source / "file.txt").write_text("hello", encoding="utf-8")

            # First run — creates the directory
            first = self.run_cli(
                "run",
                "knowledge-generator",
                "generate-knowledge",
                "--source", str(source),
                "--output-dir", str(output),
                "--yes-create-dir",
            )
            self.assertEqual(first.returncode, 0, first.stderr)

            # Second run — should fail without --yes-overwrite
            second = self.run_cli(
                "run",
                "knowledge-generator",
                "generate-knowledge",
                "--source", str(source),
                "--output-dir", str(output),
            )
        self.assertNotEqual(second.returncode, 0)


if __name__ == "__main__":
    unittest.main()
