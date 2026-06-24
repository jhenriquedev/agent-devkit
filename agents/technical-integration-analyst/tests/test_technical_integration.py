#!/usr/bin/env python3
"""Tests for technical-integration-analyst repositories and guardrails.

Covers: parsers (OpenAPI, Postman, WSDL, texto livre), mask_secrets,
guardrails de run_tests (dry-run/execute/mutation/sem base_url),
build_postman_collection v2.1 e fixture path.
"""

from __future__ import annotations

import json
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Resolve paths without installing the package
AGENT_DIR = Path(__file__).resolve().parents[1]
TECHNICAL_INTEGRATION_DIR = AGENT_DIR / "infra" / "integrations" / "technical-integration"
HTTP_API_DIR = AGENT_DIR / "infra" / "integrations" / "http-api"
DOCUMENT_SOURCE_DIR = AGENT_DIR / "infra" / "integrations" / "document-source"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

sys.path.insert(0, str(TECHNICAL_INTEGRATION_DIR))
sys.path.insert(0, str(HTTP_API_DIR))
sys.path.insert(0, str(DOCUMENT_SOURCE_DIR))

from technical_integration_repository import (  # noqa: E402
    TechnicalIntegrationRepository,
    extract_structured_operations,
    extract_text_operations,
    detect_protocols,
    detect_auth,
    identify_missing_information,
    analyze_flow,
    primary_protocol,
)
from http_api_repository import HttpApiRepository, HttpApiRepositoryError  # noqa: E402
from document_source_repository import DocumentSourceError, DocumentSourceRepository  # noqa: E402


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
RUNNER_SUPPORT_DIR = AGENT_DIR / "capabilities" / "_shared"


def load_runner_support():
    spec = importlib.util.spec_from_file_location(
        "technical_integration_runner_support",
        RUNNER_SUPPORT_DIR / "runner_support.py",
    )
    if spec is None or spec.loader is None:
        raise ImportError("cannot load technical integration runner_support")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Parser: OpenAPI
# ---------------------------------------------------------------------------

class TestOpenApiParser(unittest.TestCase):
    def setUp(self) -> None:
        openapi_path = FIXTURES_DIR / "openapi_simple.json"
        self.raw = openapi_path.read_text(encoding="utf-8")

    def test_detects_operations(self) -> None:
        ops = extract_structured_operations(self.raw, "json", "openapi_simple.json")
        methods = {op.method for op in ops}
        self.assertIn("GET", methods)
        self.assertIn("POST", methods)
        self.assertIn("DELETE", methods)

    def test_sets_protocol_rest(self) -> None:
        ops = extract_structured_operations(self.raw, "json", "openapi_simple.json")
        for op in ops:
            self.assertEqual(op.protocol, "rest")

    def test_mutation_flag(self) -> None:
        ops = extract_structured_operations(self.raw, "json", "openapi_simple.json")
        by_method = {op.method: op for op in ops}
        self.assertFalse(by_method["GET"].mutation)
        self.assertTrue(by_method["POST"].mutation)
        self.assertTrue(by_method["DELETE"].mutation)

    def test_body_example_extracted(self) -> None:
        ops = extract_structured_operations(self.raw, "json", "openapi_simple.json")
        post_ops = [op for op in ops if op.method == "POST"]
        self.assertTrue(len(post_ops) > 0)
        self.assertIsNotNone(post_ops[0].body_example)
        self.assertEqual(post_ops[0].body_example.get("name"), "test-item")

    def test_evidence_is_location(self) -> None:
        ops = extract_structured_operations(self.raw, "json", "openapi_simple.json")
        for op in ops:
            self.assertEqual(op.evidence, "openapi_simple.json")


# ---------------------------------------------------------------------------
# Parser: Postman Collection
# ---------------------------------------------------------------------------

class TestPostmanParser(unittest.TestCase):
    def setUp(self) -> None:
        postman_path = FIXTURES_DIR / "postman_simple.json"
        self.raw = postman_path.read_text(encoding="utf-8")

    def test_detects_get_and_post(self) -> None:
        ops = extract_structured_operations(self.raw, "json", "postman_simple.json")
        methods = {op.method for op in ops}
        self.assertIn("GET", methods)
        self.assertIn("POST", methods)

    def test_path_extracted(self) -> None:
        ops = extract_structured_operations(self.raw, "json", "postman_simple.json")
        paths = {op.path for op in ops}
        self.assertTrue(any("/users" in p for p in paths))


# ---------------------------------------------------------------------------
# Parser: WSDL/SOAP
# ---------------------------------------------------------------------------

class TestWsdlParser(unittest.TestCase):
    def setUp(self) -> None:
        wsdl_path = FIXTURES_DIR / "wsdl_simple.xml"
        self.raw = wsdl_path.read_text(encoding="utf-8")

    def test_detects_soap_operations(self) -> None:
        ops = extract_structured_operations(self.raw, "xml", "wsdl_simple.xml")
        names = {op.name for op in ops}
        self.assertIn("GetOrder", names)
        self.assertIn("CreateOrder", names)

    def test_protocol_is_soap(self) -> None:
        ops = extract_structured_operations(self.raw, "xml", "wsdl_simple.xml")
        for op in ops:
            self.assertEqual(op.protocol, "soap")


# ---------------------------------------------------------------------------
# Parser: texto livre (regex)
# ---------------------------------------------------------------------------

class TestTextParser(unittest.TestCase):
    def test_extracts_method_and_path(self) -> None:
        text = "Use GET /api/v1/users to list users and POST /api/v1/users to create one."
        ops = extract_text_operations(text, "text_source")
        methods = {op.method for op in ops}
        self.assertIn("GET", methods)
        self.assertIn("POST", methods)

    def test_mutation_true_for_post(self) -> None:
        ops = extract_text_operations("POST /items", "src")
        self.assertTrue(any(op.mutation for op in ops))

    def test_mutation_false_for_get(self) -> None:
        ops = extract_text_operations("GET /items", "src")
        self.assertFalse(any(op.mutation for op in ops))


# ---------------------------------------------------------------------------
# mask_secrets via DocumentSourceRepository
# ---------------------------------------------------------------------------

class TestMaskSecrets(unittest.TestCase):
    def test_masks_bearer_token(self) -> None:
        repo = DocumentSourceRepository()
        loaded = repo.load_sources(text="Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.secret")
        text = loaded["sources"][0]["text"] if loaded["sources"] else ""
        self.assertNotIn("eyJhbGciOiJIUzI1NiJ9.secret", text)

    def test_masks_api_key(self) -> None:
        repo = DocumentSourceRepository()
        loaded = repo.load_sources(text="api_key: sk-prod-ABCDEF1234567890")
        text = loaded["sources"][0]["text"] if loaded["sources"] else ""
        self.assertNotIn("sk-prod-ABCDEF1234567890", text)

    def test_masks_password(self) -> None:
        repo = DocumentSourceRepository()
        loaded = repo.load_sources(text="password: s3cr3tP@ss!")
        text = loaded["sources"][0]["text"] if loaded["sources"] else ""
        self.assertNotIn("s3cr3tP@ss!", text)


class TestDocumentSourceLimits(unittest.TestCase):
    def test_url_source_above_byte_limit_raises(self) -> None:
        repo = DocumentSourceRepository()

        class FakeResponse:
            headers = {"content-type": "text/plain"}

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *_: object) -> None:
                return None

            def read(self, size: int | None = None) -> bytes:
                data = b"x" * 11
                return data if size is None else data[:size]

        with patch.dict(os.environ, {"TECH_INTEGRATION_MAX_SOURCE_BYTES": "10"}, clear=False), patch(
            "urllib.request.urlopen", return_value=FakeResponse()
        ):
            with self.assertRaises(DocumentSourceError):
                repo.load_sources(url="https://docs.example.com/openapi.txt")

    def test_file_source_above_byte_limit_raises(self) -> None:
        repo = DocumentSourceRepository()
        with tempfile.TemporaryDirectory() as tmpdir, patch.dict(
            os.environ, {"TECH_INTEGRATION_MAX_SOURCE_BYTES": "10"}, clear=False
        ):
            path = Path(tmpdir) / "large.md"
            path.write_text("x" * 11, encoding="utf-8")

            with self.assertRaises(DocumentSourceError):
                repo.load_sources(file=str(path))

    def test_directory_above_source_count_limit_raises(self) -> None:
        repo = DocumentSourceRepository()
        with tempfile.TemporaryDirectory() as tmpdir, patch.dict(
            os.environ, {"TECH_INTEGRATION_MAX_SOURCES": "2"}, clear=False
        ):
            base = Path(tmpdir)
            for index in range(3):
                (base / f"doc-{index}.md").write_text(f"# Doc {index}", encoding="utf-8")

            with self.assertRaises(DocumentSourceError):
                repo.load_sources(directory=str(base))

    def test_directory_above_depth_limit_raises(self) -> None:
        repo = DocumentSourceRepository()
        with tempfile.TemporaryDirectory() as tmpdir, patch.dict(
            os.environ, {"TECH_INTEGRATION_MAX_DIRECTORY_DEPTH": "1"}, clear=False
        ):
            base = Path(tmpdir)
            nested = base / "level-1" / "level-2"
            nested.mkdir(parents=True)
            (nested / "deep.md").write_text("# Deep", encoding="utf-8")

            with self.assertRaises(DocumentSourceError):
                repo.load_sources(directory=str(base))


# ---------------------------------------------------------------------------
# Guardrails: run_tests (HttpApiRepository)
# ---------------------------------------------------------------------------

class TestRunTestsGuardrails(unittest.TestCase):
    def _contract_with_mutations(self) -> dict:
        return {
            "base_url": None,
            "operations": [
                {"method": "GET", "path": "/items"},
                {"method": "POST", "path": "/items"},
            ],
        }

    def test_dry_run_by_default(self) -> None:
        repo = HttpApiRepository()
        result = repo.run_tests(contract=self._contract_with_mutations())
        self.assertFalse(result["execute"])
        statuses = {r["status"] for r in result["results"]}
        self.assertIn("dry-run", statuses)

    def test_execute_without_base_url_raises(self) -> None:
        repo = HttpApiRepository()
        with self.assertRaises(HttpApiRepositoryError):
            repo.run_tests(
                contract=self._contract_with_mutations(),
                base_url=None,
                execute=True,
                confirm_mutations=True,
            )

    def test_execute_with_mutations_requires_confirm(self) -> None:
        repo = HttpApiRepository()
        with self.assertRaises(HttpApiRepositoryError):
            repo.run_tests(
                contract=self._contract_with_mutations(),
                base_url="https://sandbox.example.com",
                execute=True,
                confirm_mutations=False,
            )

    def test_dry_run_marks_mutation_flag(self) -> None:
        repo = HttpApiRepository()
        result = repo.run_tests(contract=self._contract_with_mutations())
        mutation_results = [r for r in result["results"] if r["operation"] == "POST /items"]
        self.assertTrue(len(mutation_results) > 0)
        self.assertTrue(mutation_results[0]["mutation"])

    def test_result_fields(self) -> None:
        """Return value must contain execute, base_url, results (aligns with YAML contract)."""
        repo = HttpApiRepository()
        result = repo.run_tests(contract={"base_url": None, "operations": []})
        self.assertIn("execute", result)
        self.assertIn("base_url", result)
        self.assertIn("results", result)

    def test_execute_requires_allowed_hosts(self) -> None:
        repo = HttpApiRepository()
        with self.assertRaises(HttpApiRepositoryError):
            repo.run_tests(
                contract={"base_url": "https://api.example.com", "operations": [{"method": "GET", "path": "/items"}]},
                execute=True,
            )

    def test_blocks_metadata_service_destination(self) -> None:
        repo = HttpApiRepository()
        with self.assertRaises(HttpApiRepositoryError):
            repo.run_tests(
                contract={"base_url": "http://169.254.169.254/latest/meta-data", "operations": [{"method": "GET", "path": "/"}]},
                execute=True,
                allowed_hosts=["169.254.169.254"],
            )

    def test_blocks_loopback_ip_destination(self) -> None:
        repo = HttpApiRepository()
        with self.assertRaises(HttpApiRepositoryError):
            repo.run_tests(
                contract={"base_url": "http://127.0.0.1:8080", "operations": [{"method": "GET", "path": "/health"}]},
                execute=True,
                allowed_hosts=["127.0.0.1"],
            )

    def test_blocks_localhost_destination(self) -> None:
        repo = HttpApiRepository()
        with self.assertRaises(HttpApiRepositoryError):
            repo.run_tests(
                contract={"base_url": "http://localhost:8080", "operations": [{"method": "GET", "path": "/health"}]},
                execute=True,
                allowed_hosts=["localhost"],
            )

    def test_blocks_unsupported_scheme(self) -> None:
        repo = HttpApiRepository()
        with self.assertRaises(HttpApiRepositoryError):
            repo.run_tests(
                contract={"base_url": "ftp://example.com", "operations": [{"method": "GET", "path": "/items"}]},
                execute=True,
                allowed_hosts=["example.com"],
            )

    def test_allows_https_destination_when_host_is_allowlisted(self) -> None:
        repo = HttpApiRepository()

        class FakeResponse:
            status = 200

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *_: object) -> None:
                return None

            def read(self) -> bytes:
                return b'{"ok":true}'

        with patch("socket.getaddrinfo", return_value=[]), patch("urllib.request.urlopen", return_value=FakeResponse()):
            result = repo.run_tests(
                contract={"base_url": "https://api.example.com", "operations": [{"method": "GET", "path": "/items"}]},
                execute=True,
                allowed_hosts=["api.example.com"],
            )

        self.assertEqual(result["results"][0]["status"], 200)

    def test_allowed_hosts_can_come_from_env(self) -> None:
        repo = HttpApiRepository()

        class FakeResponse:
            status = 204

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *_: object) -> None:
                return None

            def read(self) -> bytes:
                return b""

        with patch.dict(os.environ, {"TECH_INTEGRATION_ALLOWED_HOSTS": "api.example.com"}, clear=False), patch(
            "socket.getaddrinfo", return_value=[]
        ), patch("urllib.request.urlopen", return_value=FakeResponse()):
            result = repo.run_tests(
                contract={"base_url": "https://api.example.com", "operations": [{"method": "GET", "path": "/items"}]},
                execute=True,
            )

        self.assertEqual(result["results"][0]["status"], 204)

    def test_runner_accepts_allow_host_argument(self) -> None:
        module = load_runner_support()
        captured: dict[str, object] = {}

        def fake_extract_contract(args: object) -> dict:
            return {"base_url": getattr(args, "base_url"), "operations": [{"method": "GET", "path": "/items"}]}

        class FakeHttpApiRepository:
            def run_tests(self, **kwargs: object) -> dict:
                captured.update(kwargs)
                return {"execute": kwargs["execute"], "base_url": kwargs["base_url"], "results": []}

        argv = [
            "runner",
            "--text",
            "GET /items",
            "--base-url",
            "https://api.example.com",
            "--execute",
            "--allow-host",
            "api.example.com",
        ]
        with patch.object(sys, "argv", argv), patch.object(module, "extract_contract", side_effect=fake_extract_contract), patch.object(
            module, "HttpApiRepository", return_value=FakeHttpApiRepository()
        ), patch.object(module, "write_output"):
            code = module.run_integration_tests()

        self.assertEqual(code, 0)
        self.assertEqual(captured["allowed_hosts"], ["api.example.com"])


# ---------------------------------------------------------------------------
# Postman Collection v2.1
# ---------------------------------------------------------------------------

class TestBuildPostmanCollection(unittest.TestCase):
    def setUp(self) -> None:
        openapi_path = FIXTURES_DIR / "openapi_simple.json"
        raw = openapi_path.read_text(encoding="utf-8")
        sources = [{"text": raw, "raw": raw, "source_type": "json", "location": "openapi_simple.json"}]
        self.contract = TechnicalIntegrationRepository().extract_contract(sources=sources)
        self.repo = TechnicalIntegrationRepository()

    def test_schema_version(self) -> None:
        collection = self.repo.build_postman_collection(self.contract)
        self.assertIn("v2.1.0", collection["info"]["schema"])

    def test_has_variables(self) -> None:
        collection = self.repo.build_postman_collection(self.contract)
        var_keys = {v["key"] for v in collection["variable"]}
        self.assertIn("base_url", var_keys)
        self.assertIn("token", var_keys)

    def test_items_not_empty_for_http_contract(self) -> None:
        collection = self.repo.build_postman_collection(self.contract)
        self.assertTrue(len(collection["item"]) > 0)

    def test_no_real_secrets_in_collection(self) -> None:
        """Token must be empty placeholder, not a real value."""
        collection = self.repo.build_postman_collection(self.contract)
        token_vars = [v for v in collection["variable"] if v["key"] == "token"]
        self.assertTrue(len(token_vars) > 0)
        self.assertEqual(token_vars[0]["value"], "")


# ---------------------------------------------------------------------------
# Fixture path (runner_support.load_fixture)
# ---------------------------------------------------------------------------

class TestFixturePath(unittest.TestCase):
    def test_fixture_loaded_correctly(self) -> None:
        load_fixture = load_runner_support().load_fixture

        fixture_path = str(FIXTURES_DIR / "dry_run_result.json")
        result = load_fixture(fixture_path)
        self.assertIsNotNone(result)
        self.assertIn("results", result)
        self.assertFalse(result["execute"])

    def test_fixture_none_returns_none(self) -> None:
        load_fixture = load_runner_support().load_fixture

        result = load_fixture(None)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# extract_contract: fields alignment with YAML contract
# ---------------------------------------------------------------------------

class TestExtractContractFields(unittest.TestCase):
    def test_contract_includes_flow(self) -> None:
        sources = [{"text": "GET /items\nPOST /items", "raw": "GET /items\nPOST /items",
                    "source_type": "text", "location": "test"}]
        contract = TechnicalIntegrationRepository().extract_contract(sources=sources)
        self.assertIn("flow", contract)
        self.assertIsInstance(contract["flow"], list)

    def test_contract_includes_primary_protocol(self) -> None:
        sources = [{"text": "GET /items", "raw": "GET /items",
                    "source_type": "text", "location": "test"}]
        contract = TechnicalIntegrationRepository().extract_contract(sources=sources)
        self.assertIn("primary_protocol", contract)

    def test_contract_includes_missing_information(self) -> None:
        sources = [{"text": "GET /items", "raw": "GET /items",
                    "source_type": "text", "location": "test"}]
        contract = TechnicalIntegrationRepository().extract_contract(sources=sources)
        self.assertIn("missing_information", contract)
        self.assertIsInstance(contract["missing_information"], list)


# ---------------------------------------------------------------------------
# Runner support path setup (smoke test)
# ---------------------------------------------------------------------------

class TestRunnerSupportImport(unittest.TestCase):
    def test_import_runner_support(self) -> None:
        runner_support = load_runner_support()

        self.assertTrue(hasattr(runner_support, "run_ingest"))
        self.assertTrue(hasattr(runner_support, "run_extract_contract"))
        self.assertTrue(hasattr(runner_support, "render_test_report"))


if __name__ == "__main__":
    unittest.main()
