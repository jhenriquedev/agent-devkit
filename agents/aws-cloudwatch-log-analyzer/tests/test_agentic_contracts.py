#!/usr/bin/env python3
"""Agentic contract tests for AWS CloudWatch Log Analyzer."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


AGENT_DIR = Path(__file__).resolve().parents[1]


class AwsCloudWatchAgenticContractsTest(unittest.TestCase):
    def test_system_prompt_is_loaded_first(self) -> None:
        agent_yaml = read("agent.yaml")
        self.assertRegex(
            agent_yaml,
            r"default_context:\n\s+- knowledge/system\.md\n\s+- knowledge/context\.md\n\s+- knowledge/policies\.yaml",
        )
        system_prompt = read("knowledge/system.md")
        for expected in (
            "read-only",
            "fatos",
            "hipoteses",
            "dados sensiveis",
            "escopo",
            "CloudWatch Logs",
        ):
            self.assertIn(normalize(expected), normalize(system_prompt))

    def test_prompts_are_not_stubs(self) -> None:
        prompts_dir = AGENT_DIR / "knowledge" / "prompts"
        prompt_files = [
            path
            for path in prompts_dir.glob("*.md")
            if path.name != "README.md"
        ]
        expected = {
            "analyze-service-error.md",
            "correlate-azure-card-logs.md",
            "detect-error-patterns.md",
            "extract-log-samples.md",
            "generate-incident-report.md",
            "list-log-groups.md",
            "list-log-streams.md",
            "run-insights-query.md",
            "search-log-events.md",
            "trace-request.md",
        }
        self.assertEqual({path.name for path in prompt_files}, expected)
        for path in prompt_files:
            with self.subTest(prompt=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertGreaterEqual(len(text.splitlines()), 18)
                for section in ("## Objetivo", "## Entradas", "## Regras", "## Saida", "## Nao faca"):
                    self.assertIn(section, text)
                self.assertIsNone(re.search(r"\bTODO\b", text.upper()))

    def test_all_repository_methods_are_backed_by_capabilities(self) -> None:
        methods_dir = AGENT_DIR / "infra" / "integrations" / "aws-cloudwatch" / "methods"
        method_files = {path.name for path in methods_dir.glob("*.yaml")}
        referenced_methods: set[str] = set()
        for capability_yaml in (AGENT_DIR / "capabilities").glob("*/capability.yaml"):
            text = capability_yaml.read_text(encoding="utf-8")
            referenced_methods.update(re.findall(r"methods/([^/\s]+\.yaml)", text))
        self.assertEqual(method_files, referenced_methods)

    def test_sensitive_trace_and_azure_correlation_limits_are_documented(self) -> None:
        trace_rules = normalize(read("capabilities/trace-request/decision-rules.md"))
        for expected in ("pii", "segredo", "token", "mascar", "identificador"):
            self.assertIn(expected, trace_rules)

        correlate_rules = normalize(read("capabilities/correlate-azure-card-logs/decision-rules.md"))
        for expected in ("azure devops", "fixture", "nao le", "nenhuma escrita"):
            self.assertIn(expected, correlate_rules)

    def test_conditional_capability_inputs_are_explicit(self) -> None:
        insights_manifest = read("capabilities/run-insights-query/capability.yaml")
        self.assertEqual(required_inputs(insights_manifest), {"region"})
        self.assertIn("input_modes:", insights_manifest)
        for expected in ("start_query", "get_results", "log_group", "start_time", "end_time", "query", "query_id"):
            self.assertIn(expected, insights_manifest)

        correlate_manifest = read("capabilities/correlate-azure-card-logs/capability.yaml")
        self.assertEqual(
            required_inputs(correlate_manifest),
            {"azure_project", "work_item_id", "region", "log_group", "start_time", "end_time"},
        )


def read(relative_path: str) -> str:
    return (AGENT_DIR / relative_path).read_text(encoding="utf-8")


def required_inputs(manifest: str) -> set[str]:
    match = re.search(r"inputs:\n\s+required:\n(?P<body>(?:\s{4}- .+\n)+)", manifest)
    if not match:
        return set()
    return {line.strip()[2:] for line in match.group("body").splitlines()}


def normalize(value: str) -> str:
    text = value.lower()
    replacements = {
        "á": "a",
        "à": "a",
        "ã": "a",
        "â": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


if __name__ == "__main__":
    unittest.main()
