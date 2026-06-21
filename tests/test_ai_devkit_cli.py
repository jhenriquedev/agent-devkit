#!/usr/bin/env python3
"""Tests for the root ai-devkit CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "ai-devkit"


class AiDevKitCliTest(unittest.TestCase):
    def test_lists_available_agents(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CLI), "--json", "agents"],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        agents = {item["id"] for item in payload["items"]}
        self.assertIn("azure-devops-orchestrator", agents)
        self.assertIn("aws-cloudwatch-log-analyzer", agents)
        self.assertIn("database-change-operator", agents)
        self.assertIn("elasticsearch-log-analyzer", agents)
        self.assertIn("postgres-data-analyzer", agents)
        self.assertIn("sqlserver-data-analyzer", agents)
        self.assertIn("sqlserver-change-operator", agents)
        self.assertIn("software-specification-analyst", agents)
        self.assertIn("technical-integration-analyst", agents)
        self.assertIn("topdesk-orchestrator", agents)

    def test_lists_all_software_specification_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "software-specification-analyst",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        capabilities = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertEqual(
            capabilities,
            {
                "analyze-multiple-projects",
                "analyze-project-context",
                "build-requirements-traceability",
                "conduct-requirements-interview",
                "create-analysis-dossier",
                "create-complete-spec",
                "create-discovery-notes",
                "create-functional-spec",
                "create-technical-spec",
                "create-final-spec-from-analysis",
                "identify-business-questions",
                "identify-critical-points",
                "map-user-journeys",
                "refine-analysis-with-feedback",
                "review-spec-completeness",
                "write-user-stories",
            },
        )

    def test_software_specification_create_complete_spec_has_runner(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "inspect",
                "software-specification-analyst",
                "create-complete-spec",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        runner = payload["capability"]["entrypoint"]["runner"]
        self.assertTrue(runner["exists"])

    def test_software_specification_analyze_project_context_has_runner(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "inspect",
                "software-specification-analyst",
                "analyze-project-context",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        runner = payload["capability"]["entrypoint"]["runner"]
        self.assertTrue(runner["exists"])

    def test_run_analyze_project_context_creates_analysis_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "sample-app"
            source_dir = project_dir / "src"
            source_dir.mkdir(parents=True)
            (project_dir / "README.md").write_text(
                "# Sample App\n\nAPI para abrir solicitacoes.",
                encoding="utf-8",
            )
            (project_dir / "package.json").write_text(
                '{"scripts":{"test":"vitest"},"dependencies":{"express":"latest"}}',
                encoding="utf-8",
            )
            (source_dir / "tickets.ts").write_text(
                "export function createTicket(userId: string) { return { userId, status: 'open' }; }",
                encoding="utf-8",
            )
            output_dir = Path(tmpdir) / "analysis-output"

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "software-specification-analyst",
                    "analyze-project-context",
                    "--project",
                    str(project_dir),
                    "--output-dir",
                    str(output_dir),
                    "--yes-create-dir",
                    "--depth",
                    "medium",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output_dir / "analysis-context.md").exists())
            self.assertTrue((output_dir / "business-questions.md").exists())
            self.assertTrue((output_dir / "critical-points.md").exists())
            analysis = (output_dir / "analysis-context.md").read_text(encoding="utf-8")
            questions = (output_dir / "business-questions.md").read_text(encoding="utf-8")
            self.assertIn("sample-app", analysis)
            self.assertIn("package.json", analysis)
            self.assertIn("solicitacoes", questions)

    def test_run_create_complete_spec_with_explicit_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "demanda.md"
            output_dir = Path(tmpdir) / "spec-output"
            input_path.write_text(
                "# Portal de atendimento\n\nUsuario abre solicitacoes e acompanha status.",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "software-specification-analyst",
                    "create-complete-spec",
                    "--input",
                    str(input_path),
                    "--output-dir",
                    str(output_dir),
                    "--yes-create-dir",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output_dir / "software-specification.md").exists())
            self.assertTrue((output_dir / "functional-spec.md").exists())
            self.assertTrue((output_dir / "technical-spec.md").exists())
            self.assertIn("Artefatos gerados em:", result.stdout)

    def test_lists_all_database_change_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "database-change-operator",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        capabilities = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertEqual(
            capabilities,
            {
                "apply-migration",
                "migration-report",
                "plan-migration",
                "rollback-migration",
                "run-write-script",
                "test-write-permissions",
                "update-records",
                "upsert-records",
            },
        )

    def test_all_database_change_capabilities_have_runner(self) -> None:
        for capability in (
            "apply-migration",
            "migration-report",
            "plan-migration",
            "rollback-migration",
            "run-write-script",
            "test-write-permissions",
            "update-records",
            "upsert-records",
        ):
            with self.subTest(capability=capability):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--json",
                        "inspect",
                        "database-change-operator",
                        capability,
                    ],
                    cwd=ROOT,
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                runner = payload["capability"]["entrypoint"]["runner"]
                self.assertTrue(runner["exists"])

    def test_lists_all_sqlserver_change_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "sqlserver-change-operator",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        capabilities = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertEqual(
            capabilities,
            {
                "apply-migration",
                "backup-records",
                "change-report",
                "create-object",
                "delete-records",
                "plan-migration",
                "rollback-migration",
                "run-write-script",
                "test-write-permissions",
                "update-records",
                "upsert-records",
            },
        )

    def test_all_sqlserver_change_capabilities_have_runner(self) -> None:
        for capability in (
            "apply-migration",
            "backup-records",
            "change-report",
            "create-object",
            "delete-records",
            "plan-migration",
            "rollback-migration",
            "run-write-script",
            "test-write-permissions",
            "update-records",
            "upsert-records",
        ):
            with self.subTest(capability=capability):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--json",
                        "inspect",
                        "sqlserver-change-operator",
                        capability,
                    ],
                    cwd=ROOT,
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                runner = payload["capability"]["entrypoint"]["runner"]
                self.assertTrue(runner["exists"])

    def test_postgres_capabilities_expose_database_optional_input(self) -> None:
        for agent, capability in (
            ("postgres-data-analyzer", "list-tables"),
            ("database-change-operator", "migration-report"),
        ):
            with self.subTest(agent=agent, capability=capability):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--json",
                        "inspect",
                        agent,
                        capability,
                    ],
                    cwd=ROOT,
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                optional = payload["capability"]["inputs"]["optional"]
                self.assertIn("database", optional)

    def test_lists_all_postgres_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "postgres-data-analyzer",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        capabilities = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertEqual(
            capabilities,
            {
                "analyze-cpf-column",
                "describe-table",
                "detect-sensitive-columns",
                "generate-data-report",
                "list-schemas",
                "list-tables",
                "profile-table",
                "run-readonly-query",
                "test-connection",
            },
        )

    def test_all_postgres_capabilities_have_runner(self) -> None:
        for capability in (
            "analyze-cpf-column",
            "describe-table",
            "detect-sensitive-columns",
            "generate-data-report",
            "list-schemas",
            "list-tables",
            "profile-table",
            "run-readonly-query",
            "test-connection",
        ):
            with self.subTest(capability=capability):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--json",
                        "inspect",
                        "postgres-data-analyzer",
                        capability,
                    ],
                    cwd=ROOT,
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                runner = payload["capability"]["entrypoint"]["runner"]
                self.assertTrue(runner["exists"])

    def test_lists_all_elasticsearch_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "elasticsearch-log-analyzer",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        capabilities = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertEqual(
            capabilities,
            {
                "analyze-service-errors",
                "correlate-azure-card-logs",
                "detect-error-patterns",
                "extract-log-samples",
                "generate-log-report",
                "list-log-sources",
                "search-log-events",
                "trace-request",
            },
        )

    def test_all_elasticsearch_capabilities_have_runner(self) -> None:
        for capability in (
            "analyze-service-errors",
            "correlate-azure-card-logs",
            "detect-error-patterns",
            "extract-log-samples",
            "generate-log-report",
            "list-log-sources",
            "search-log-events",
            "trace-request",
        ):
            with self.subTest(capability=capability):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--json",
                        "inspect",
                        "elasticsearch-log-analyzer",
                        capability,
                    ],
                    cwd=ROOT,
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                runner = payload["capability"]["entrypoint"]["runner"]
                self.assertTrue(runner["exists"])

    def test_lists_all_topdesk_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "topdesk-orchestrator",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        capabilities = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertEqual(
            capabilities,
            {
                "analyze-incident-insufficiency",
                "create-incident",
                "incident-report",
                "list-incidents",
                "read-incident",
                "request-more-info",
                "update-incident",
            },
        )

    def test_all_topdesk_capabilities_have_runner(self) -> None:
        for capability in (
            "analyze-incident-insufficiency",
            "create-incident",
            "incident-report",
            "list-incidents",
            "read-incident",
            "request-more-info",
            "update-incident",
        ):
            with self.subTest(capability=capability):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--json",
                        "inspect",
                        "topdesk-orchestrator",
                        capability,
                    ],
                    cwd=ROOT,
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                runner = payload["capability"]["entrypoint"]["runner"]
                self.assertTrue(runner["exists"])

    def test_lists_all_aws_cloudwatch_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "aws-cloudwatch-log-analyzer",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        capabilities = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertEqual(
            capabilities,
            {
                "analyze-service-error",
                "correlate-azure-card-logs",
                "detect-error-patterns",
                "extract-log-samples",
                "generate-incident-report",
                "list-log-groups",
                "search-log-events",
                "trace-request",
            },
        )

    def test_all_aws_cloudwatch_capabilities_have_runner(self) -> None:
        for capability in (
            "analyze-service-error",
            "correlate-azure-card-logs",
            "detect-error-patterns",
            "extract-log-samples",
            "generate-incident-report",
            "list-log-groups",
            "search-log-events",
            "trace-request",
        ):
            with self.subTest(capability=capability):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--json",
                        "inspect",
                        "aws-cloudwatch-log-analyzer",
                        capability,
                    ],
                    cwd=ROOT,
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                runner = payload["capability"]["entrypoint"]["runner"]
                self.assertTrue(runner["exists"])

    def test_lists_all_azure_devops_capabilities(self) -> None:
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
        capabilities = {item["id"].split(".")[-1] for item in payload["items"]}
        self.assertEqual(
            capabilities,
            {
                "update-card-tags",
                "assign-card",
                "comment-card",
                "generate-cards-report",
                "read-card",
                "list-cards",
                "move-card",
                "prepare-card-analysis",
            },
        )

    def test_all_azure_devops_capabilities_have_runner(self) -> None:
        for capability in (
            "update-card-tags",
            "assign-card",
            "comment-card",
            "generate-cards-report",
            "read-card",
            "list-cards",
            "move-card",
            "prepare-card-analysis",
        ):
            with self.subTest(capability=capability):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--json",
                        "inspect",
                        "azure-devops-orchestrator",
                        capability,
                    ],
                    cwd=ROOT,
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                runner = payload["capability"]["entrypoint"]["runner"]
                self.assertTrue(runner["exists"])

    def test_run_read_card_with_fixture(self) -> None:
        fixture = {
            "work_item": {
                "id": 456,
                "work_item_type": "Bug",
                "title": "Corrigir erro no login",
                "state": "New",
                "assigned_to": "bia@example.com",
                "tags": ["bug"],
                "description": "Login falha quando o token expira.",
                "acceptance_criteria": "Usuario deve ser redirecionado para autenticar novamente.",
            },
            "comments": {"work_item_id": 456, "count": 0, "comments": []},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "card.json"
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "azure-devops-orchestrator",
                    "read-card",
                    "--project",
                    "Projeto A",
                    "--fixture",
                    str(fixture_path),
                    "--include-comments",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Card Analysis", result.stdout)
        self.assertIn("- ID: 456", result.stdout)
        self.assertIn("- Title: Corrigir erro no login", result.stdout)


if __name__ == "__main__":
    unittest.main()
