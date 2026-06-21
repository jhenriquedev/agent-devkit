#!/usr/bin/env python3
"""Shared helpers for Technical Integration Analyst runners."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
DOCUMENT_SOURCE_DIR = AGENT_DIR / "infra" / "integrations" / "document-source"
TECHNICAL_INTEGRATION_DIR = AGENT_DIR / "infra" / "integrations" / "technical-integration"
HTTP_API_DIR = AGENT_DIR / "infra" / "integrations" / "http-api"

sys.path.insert(0, str(DOCUMENT_SOURCE_DIR))
sys.path.insert(0, str(TECHNICAL_INTEGRATION_DIR))
sys.path.insert(0, str(HTTP_API_DIR))

from document_source_repository import DocumentSourceRepository  # pylint: disable=import-error
from http_api_repository import HttpApiRepository  # pylint: disable=import-error
from technical_integration_repository import TechnicalIntegrationRepository, write_json  # pylint: disable=import-error


def add_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--url")
    parser.add_argument("--file")
    parser.add_argument("--directory")
    parser.add_argument("--text")
    parser.add_argument("--base-url")


def add_output_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output")


def load_sources(args: argparse.Namespace) -> dict[str, Any]:
    return DocumentSourceRepository().load_sources(
        url=args.url,
        file=args.file,
        directory=args.directory,
        text=args.text,
    )


def extract_contract(args: argparse.Namespace) -> dict[str, Any]:
    loaded = load_sources(args)
    return TechnicalIntegrationRepository().extract_contract(
        sources=loaded["sources"],
        base_url=args.base_url,
    )


def write_output(markdown: str, output: str | None) -> None:
    if output:
        Path(output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)


def print_error(exc: Exception) -> int:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1


def load_fixture(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_ingest() -> int:
    parser = argparse.ArgumentParser(description="Run technical-integration-analyst/ingest-technical-docs")
    add_source_args(parser)
    add_output_arg(parser)
    args = parser.parse_args()
    try:
        loaded = load_sources(args)
        markdown = TechnicalIntegrationRepository().render_ingestion_markdown(loaded)
        write_output(markdown, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def run_extract_contract() -> int:
    parser = argparse.ArgumentParser(description="Run technical-integration-analyst/extract-integration-contract")
    add_source_args(parser)
    parser.add_argument("--contract-output")
    add_output_arg(parser)
    args = parser.parse_args()
    try:
        repo = TechnicalIntegrationRepository()
        contract = extract_contract(args)
        if args.contract_output:
            write_json(args.contract_output, contract)
        write_output(repo.render_contract_markdown(contract), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def run_missing_information() -> int:
    parser = argparse.ArgumentParser(description="Run technical-integration-analyst/identify-missing-information")
    add_source_args(parser)
    add_output_arg(parser)
    args = parser.parse_args()
    try:
        repo = TechnicalIntegrationRepository()
        write_output(repo.render_missing_information(extract_contract(args)), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def run_flow() -> int:
    parser = argparse.ArgumentParser(description="Run technical-integration-analyst/analyze-integration-flow")
    add_source_args(parser)
    add_output_arg(parser)
    args = parser.parse_args()
    try:
        repo = TechnicalIntegrationRepository()
        write_output(repo.render_flow(extract_contract(args)), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def run_test_data() -> int:
    parser = argparse.ArgumentParser(description="Run technical-integration-analyst/generate-test-data")
    add_source_args(parser)
    parser.add_argument("--json-output")
    add_output_arg(parser)
    args = parser.parse_args()
    try:
        repo = TechnicalIntegrationRepository()
        test_data = repo.generate_test_data(extract_contract(args))
        if args.json_output:
            write_json(args.json_output, test_data)
        write_output(repo.render_test_data(test_data), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def run_http_artifacts() -> int:
    parser = argparse.ArgumentParser(description="Run technical-integration-analyst/generate-http-artifacts")
    add_source_args(parser)
    parser.add_argument("--postman-output")
    add_output_arg(parser)
    args = parser.parse_args()
    try:
        repo = TechnicalIntegrationRepository()
        contract = extract_contract(args)
        if args.postman_output:
            write_json(args.postman_output, repo.build_postman_collection(contract))
        write_output(repo.render_http_artifacts(contract), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def run_protocol_artifacts() -> int:
    parser = argparse.ArgumentParser(description="Run technical-integration-analyst/generate-protocol-artifacts")
    add_source_args(parser)
    add_output_arg(parser)
    args = parser.parse_args()
    try:
        repo = TechnicalIntegrationRepository()
        write_output(repo.render_protocol_artifacts(extract_contract(args)), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def run_integration_tests() -> int:
    parser = argparse.ArgumentParser(description="Run technical-integration-analyst/run-integration-tests")
    add_source_args(parser)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-mutations", action="store_true")
    parser.add_argument("--fixture")
    add_output_arg(parser)
    args = parser.parse_args()
    try:
        fixture = load_fixture(args.fixture)
        if fixture:
            result = fixture
        else:
            contract = extract_contract(args)
            result = HttpApiRepository().run_tests(
                contract=contract,
                base_url=args.base_url,
                execute=args.execute,
                confirm_mutations=args.confirm_mutations,
            )
        write_output(render_test_report(result), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def run_technical_docs() -> int:
    parser = argparse.ArgumentParser(description="Run technical-integration-analyst/generate-technical-docs")
    add_source_args(parser)
    parser.add_argument("--md-output")
    parser.add_argument("--pdf-output")
    add_output_arg(parser)
    args = parser.parse_args()
    try:
        repo = TechnicalIntegrationRepository()
        markdown = repo.render_technical_docs(extract_contract(args))
        if args.md_output:
            Path(args.md_output).write_text(markdown, encoding="utf-8")
        if args.pdf_output:
            repo.write_pdf(markdown, args.pdf_output)
        write_output(markdown, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def render_test_report(result: dict[str, Any]) -> str:
    lines = [
        "# Plano de Testes de Integracao",
        "",
        f"- Execucao real: {result.get('execute', False)}",
        f"- Base URL: {result.get('base_url') or '{{base_url}}'}",
        "",
        "## Operacoes",
        "",
    ]
    for item in result.get("results") or []:
        lines.append(f"- {item.get('operation')}: {item.get('status')}")
    if not result.get("results"):
        lines.append("- Nenhuma operacao executavel detectada.")
    return "\n".join(lines).rstrip() + "\n"
