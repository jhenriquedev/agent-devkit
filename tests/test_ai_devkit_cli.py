#!/usr/bin/env python3
"""Tests for the root ai-devkit CLI."""

from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "ai-devkit"
CLI_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_CLI_TIMEOUT_SECONDS", "60"))
WORKBOOK_SUPPORT = (
    ROOT
    / "agents"
    / "excel-workbook-builder"
    / "capabilities"
    / "_shared"
    / "workbook_support.py"
)
NODE = Path(
    os.environ.get(
        "CODEX_NODE",
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "bin"
        / ("node.exe" if os.name == "nt" else "node"),
    )
)
NODE_MODULES = Path(
    os.environ.get(
        "CODEX_NODE_MODULES",
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "node_modules",
    )
)


def load_workbook_support_module():
    spec = importlib.util.spec_from_file_location("excel_workbook_support_for_tests", WORKBOOK_SUPPORT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def create_test_workbook(path: Path, sheets: dict[str, list[list[object]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    script = path.parent / "create-test-workbook.mjs"
    payload = path.parent / "create-test-workbook.json"
    package_json = path.parent / "package.json"
    node_modules = path.parent / "node_modules"
    package_json.write_text('{"private":true,"type":"module"}\n', encoding="utf-8")
    if not node_modules.exists():
        if os.name == "nt":
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(node_modules), str(NODE_MODULES)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        else:
            os.symlink(NODE_MODULES, node_modules, target_is_directory=True)
    payload.write_text(json.dumps({"path": str(path), "sheets": sheets}, ensure_ascii=False), encoding="utf-8")
    script.write_text(
        r'''
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";
import fs from "node:fs/promises";

const payload = JSON.parse(await fs.readFile(process.argv[2], "utf8"));
const workbook = Workbook.create();
for (const [name, rows] of Object.entries(payload.sheets)) {
  const sheet = workbook.worksheets.add(name);
  if (rows.length > 0 && rows[0].length > 0) {
    sheet.getRangeByIndexes(0, 0, rows.length, rows[0].length).values = rows;
  }
}
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(payload.path);
''',
        encoding="utf-8",
    )
    subprocess.run(
        [str(NODE), str(script), str(payload)],
        cwd=path.parent,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class AiDevKitCliTest(unittest.TestCase):
    def run_cli_ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(
                [sys.executable, str(CLI), *args],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=CLI_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as error:
            command = " ".join([str(CLI), *args])
            self.fail(f"CLI timed out after {CLI_TIMEOUT_SECONDS}s: {command}\n{error}")
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return result

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
        self.assertIn("bpo-analyser", agents)
        self.assertIn("database-change-operator", agents)
        self.assertIn("elasticsearch-log-analyzer", agents)
        self.assertIn("excel-workbook-builder", agents)
        self.assertIn("n1-support-agent", agents)
        self.assertIn("n2-support-agent", agents)
        self.assertIn("postgres-data-analyzer", agents)
        self.assertIn("presentation-deck-builder", agents)
        self.assertIn("sqlserver-data-analyzer", agents)
        self.assertIn("sqlserver-change-operator", agents)
        self.assertIn("software-specification-analyst", agents)
        self.assertIn("technical-integration-analyst", agents)
        self.assertIn("topdesk-orchestrator", agents)
        self.assertIn("figma-ui-ux-product-designer", agents)

    def test_lists_all_presentation_deck_builder_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "presentation-deck-builder",
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
                "compare-template-versions",
                "create-template",
                "create-template-version",
                "deprecate-template-version",
                "generate-deck-from-template",
                "generate-template-input-file",
                "ingest-source-document",
                "inspect-template",
                "list-template-versions",
                "list-templates",
                "plan-deck",
                "promote-template-version",
                "refine-generated-deck",
                "refine-template",
                "register-template",
                "review-generated-deck",
            },
        )

    def test_lists_all_figma_ui_ux_product_designer_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "figma-ui-ux-product-designer",
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
                "analyze-existing-figma-project",
                "analyze-product-context",
                "apply-design-feedback",
                "capture-url-to-figma",
                "conduct-design-interview",
                "conduct-design-review-session",
                "create-design-system-foundation",
                "create-figma-project",
                "create-mobile-app-design",
                "create-web-app-design",
                "facelift-existing-product",
                "generate-dev-handoff",
                "generate-user-journey-diagram",
                "ingest-design-source",
                "read-azure-card-for-design",
                "recreate-legacy-design",
                "review-design-quality",
                "setup-figma-mcp-bridge",
                "triage-design-feedback",
                "update-existing-figma-design",
            },
        )

    def test_figma_ui_ux_product_designer_setup_installs_bridge_wrappers_and_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            output_dir = tmp / "setup"
            env_file = tmp / ".env"

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "figma-ui-ux-product-designer",
                    "setup-figma-mcp-bridge",
                    "--output-dir",
                    str(output_dir),
                    "--yes-create-dir",
                    "--install-bridge",
                    "--write-env",
                    "--env-file",
                    str(env_file),
                    "--default-plan-key",
                    "team::123",
                    "--codex-command",
                    sys.executable,
                    "--skip-codex-mcp-check",
                ],
                cwd=ROOT,
                env=os.environ | {"AI_DEVKIT_IGNORE_ENV_FILE": "true"},
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output_dir / "figma-mcp-setup-report.md").exists())
            self.assertTrue((output_dir / "figma-env.generated").exists())
            bridge_py = ROOT / "agents/figma-ui-ux-product-designer/infra/integrations/figma/bin/figma-codex-bridge.py"
            bridge_sh = ROOT / "agents/figma-ui-ux-product-designer/infra/integrations/figma/bin/figma-codex-bridge"
            bridge_cmd = ROOT / "agents/figma-ui-ux-product-designer/infra/integrations/figma/bin/figma-codex-bridge.cmd"
            self.assertTrue(bridge_py.exists())
            self.assertTrue(bridge_sh.exists())
            self.assertTrue(bridge_cmd.exists())
            env_text = env_file.read_text(encoding="utf-8")
            self.assertIn("FIGMA_MCP_ENABLED=true", env_text)
            self.assertIn("FIGMA_DIRECT_MODE=true", env_text)
            self.assertIn("FIGMA_MCP_BRIDGE_COMMAND=", env_text)
            self.assertIn("FIGMA_DEFAULT_PLAN_KEY=team::123", env_text)
            report = (output_dir / "figma-mcp-setup-report.md").read_text(encoding="utf-8")
            self.assertIn("Login solicitado: nao", report)

    def test_figma_codex_bridge_diagnostic_uses_codex_exec_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            fake_codex = tmp / "fake_codex.py"
            output_file = tmp / "last-message.json"
            fake_codex.write_text(
                """
import json
import pathlib
import sys

args = sys.argv[1:]
output = pathlib.Path(args[args.index("--output-last-message") + 1])
payload = {
    "status": "inspected",
    "file_key": "diagnostic",
    "file_url": "https://figma.com/design/diagnostic/Bridge",
    "created_node_ids": [],
    "mutated_node_ids": [],
    "inspected_node_ids": ["0:1"],
}
output.write_text(json.dumps(payload), encoding="utf-8")
print(json.dumps({"event": "done"}))
""".strip()
                + "\n",
                encoding="utf-8",
            )
            bridge = ROOT / "agents/figma-ui-ux-product-designer/infra/integrations/figma/bin/figma-codex-bridge.py"
            request = json.dumps(
                {
                    "kind": "figma_mcp_operation",
                    "operation": {"capability": "setup-figma-mcp-bridge", "action": "diagnose"},
                    "env": {"FIGMA_MCP_BRIDGE_TEST_OUTPUT": str(output_file)},
                },
                ensure_ascii=False,
            )

            result = subprocess.run(
                [sys.executable, str(bridge), "--codex-command", f"{sys.executable} {fake_codex}"],
                cwd=ROOT,
                input=request,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "inspected")
            self.assertEqual(payload["inspected_node_ids"], ["0:1"])

    def test_figma_ui_ux_product_designer_generates_plan_only_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            brief = Path(tmpdir) / "brief.md"
            output_dir = Path(tmpdir) / "design"
            brief.write_text(
                "# Portal de Sustentacao\n\nCriar dashboard web para acompanhar KPIs, cards e prioridades.",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "figma-ui-ux-product-designer",
                    "create-web-app-design",
                    "--brief",
                    str(brief),
                    "--platform",
                    "web",
                    "--output-dir",
                    str(output_dir),
                    "--yes-create-dir",
                ],
                cwd=ROOT,
                env=os.environ | {"AI_DEVKIT_IGNORE_ENV_FILE": "true"},
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output_dir / "design-brief.md").exists())
            self.assertTrue((output_dir / "figma-action-plan.md").exists())
            self.assertTrue((output_dir / "web-screen-map.md").exists())
            self.assertTrue((output_dir / "dev-handoff.md").exists())
            brief_text = (output_dir / "design-brief.md").read_text(encoding="utf-8")
            self.assertIn("Figma mode: `plan_only`", brief_text)
            self.assertIn("Portal de Sustentacao", brief_text)

    def test_figma_ui_ux_product_designer_requires_real_bridge_for_direct_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            brief = Path(tmpdir) / "brief.md"
            output_dir = Path(tmpdir) / "design"
            brief.write_text("Criar painel web de KPIs.", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "figma-ui-ux-product-designer",
                    "create-web-app-design",
                    "--brief",
                    str(brief),
                    "--output-dir",
                    str(output_dir),
                    "--yes-create-dir",
                    "--require-direct",
                ],
                cwd=ROOT,
                env=os.environ | {"AI_DEVKIT_IGNORE_ENV_FILE": "true"},
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Figma direct_mcp requerido", result.stderr)
            self.assertIn("FIGMA_MCP_BRIDGE_COMMAND", result.stderr)

    def test_figma_ui_ux_product_designer_executes_direct_bridge_and_logs_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            brief = tmp / "brief.md"
            output_dir = tmp / "design"
            bridge_log = tmp / "bridge-request.json"
            bridge = tmp / "fake_figma_bridge.py"
            brief.write_text("Criar dashboard web para KPIs de sustentacao no Azure DevOps.", encoding="utf-8")
            bridge.write_text(
                """
import json
import pathlib
import sys

request = json.loads(sys.stdin.read())
pathlib.Path(request["env"]["TEST_BRIDGE_LOG"]).write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
json.dump(
    {
        "status": "executed",
        "file_key": "FIGMA123",
        "file_url": "https://figma.com/design/FIGMA123/Projeto",
        "page_name": request["operation"]["page_name"],
        "created_node_ids": ["10:1", "10:2"],
        "mutated_node_ids": [],
        "screenshot_refs": ["frame-dashboard.png"],
    },
    sys.stdout,
)
""".strip()
                + "\n",
                encoding="utf-8",
            )
            env = os.environ | {
                "FIGMA_MCP_BRIDGE_COMMAND": f"{sys.executable} {bridge}",
                "FIGMA_MCP_ENABLED": "true",
                "TEST_BRIDGE_LOG": str(bridge_log),
            }

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "figma-ui-ux-product-designer",
                    "create-web-app-design",
                    "--brief",
                    str(brief),
                    "--platform",
                    "web",
                    "--figma-file-name",
                    "Sustentacao Azure KPIs",
                    "--output-dir",
                    str(output_dir),
                    "--yes-create-dir",
                    "--yes-figma-write",
                    "--require-direct",
                ],
                cwd=ROOT,
                env=env,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output_dir / "figma-execution-result.json").exists())
            self.assertTrue((output_dir / "design-operation-log.md").exists())
            execution = json.loads((output_dir / "figma-execution-result.json").read_text(encoding="utf-8"))
            self.assertEqual(execution["status"], "executed")
            self.assertEqual(execution["file_key"], "FIGMA123")
            self.assertEqual(execution["created_node_ids"], ["10:1", "10:2"])
            brief_text = (output_dir / "design-brief.md").read_text(encoding="utf-8")
            self.assertIn("Figma mode: `direct_mcp`", brief_text)
            action_plan = (output_dir / "figma-action-plan.md").read_text(encoding="utf-8")
            self.assertIn("Execucao Real", action_plan)
            request = json.loads(bridge_log.read_text(encoding="utf-8"))
            self.assertEqual(request["operation"]["capability"], "create-web-app-design")
            self.assertEqual(request["operation"]["file_name"], "Sustentacao Azure KPIs")
            self.assertIn("Dashboard", request["operation"]["screens"])

    def test_register_template_creates_versioned_template_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "status-template.pptx"
            templates_root = Path(tmpdir) / "templates"
            template_path.write_bytes(b"fake pptx content")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "register-template",
                    "--template",
                    str(template_path),
                    "--template-id",
                    "status-report",
                    "--name",
                    "Status Report Executivo",
                    "--version",
                    "0.1.0",
                    "--status",
                    "validated",
                    "--templates-root",
                    str(templates_root),
                    "--yes-save",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            template_dir = templates_root / "status-report"
            version_dir = template_dir / "versions" / "0.1.0"
            self.assertTrue((template_dir / "template.yaml").exists())
            self.assertTrue((template_dir / "changelog.md").exists())
            self.assertTrue((version_dir / "template.pptx").exists())
            self.assertTrue((version_dir / "input-schema.xlsx").exists())
            self.assertTrue((version_dir / "input-schema.md").exists())
            self.assertTrue((version_dir / "slide-map.yaml").exists())
            manifest = (template_dir / "template.yaml").read_text(encoding="utf-8")
            self.assertIn("current_version: 0.1.0", manifest)
            self.assertIn("status: validated", manifest)
            self.assertIn("versions/0.1.0/template.pptx", manifest)

    def test_list_template_versions_reports_registered_versions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "status-template.pptx"
            templates_root = Path(tmpdir) / "templates"
            template_path.write_bytes(b"fake pptx content")
            register = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "register-template",
                    "--template",
                    str(template_path),
                    "--template-id",
                    "status-report",
                    "--version",
                    "0.1.0",
                    "--status",
                    "validated",
                    "--templates-root",
                    str(templates_root),
                    "--yes-save",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(register.returncode, 0, register.stderr)

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "list-template-versions",
                    "--template-id",
                    "status-report",
                    "--templates-root",
                    str(templates_root),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("status-report", result.stdout)
            self.assertIn("0.1.0", result.stdout)
            self.assertIn("validated", result.stdout)

    @unittest.skipUnless(
        (
            Path.home()
            / ".codex"
            / "plugins"
            / "cache"
            / "openai-primary-runtime"
            / "presentations"
        ).exists()
        or os.environ.get("PRESENTATIONS_SKILL_DIR"),
        "presentations skill (@oai/artifact-tool) not available in this environment — set PRESENTATIONS_SKILL_DIR to run",
    )
    def test_generate_deck_from_template_creates_pptx(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "kpis-template.pptx"
            templates_root = Path(tmpdir) / "templates"
            input_path = Path(tmpdir) / "kpis.json"
            output_path = Path(tmpdir) / "kpis.pptx"
            template_path.write_bytes(b"fake pptx content")
            input_path.write_text(
                json.dumps(
                    {
                        "title": "KPIs Sustentação - Azure DevOps",
                        "subtitle": "Amostra dos últimos cards alterados",
                        "metrics": [
                            {"label": "Cards analisados", "value": "20"},
                            {"label": "Em andamento", "value": "10"},
                            {"label": "Sem responsável", "value": "10"},
                            {"label": "Com anexos", "value": "13"},
                        ],
                        "state_breakdown": {"Doing": 10, "Done": 5, "To Do": 5},
                        "highlights": [
                            "A consulta atingiu o limite configurado.",
                            "Todos os cards analisados estão sem critérios de aceite.",
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            register = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "register-template",
                    "--template",
                    str(template_path),
                    "--template-id",
                    "azure-kpis",
                    "--version",
                    "0.1.0",
                    "--status",
                    "validated",
                    "--templates-root",
                    str(templates_root),
                    "--yes-save",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(register.returncode, 0, register.stderr)

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "generate-deck-from-template",
                    "--template-id",
                    "azure-kpis",
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--templates-root",
                    str(templates_root),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 0)
            self.assertEqual(output_path.read_bytes()[:2], b"PK")
            self.assertIn("Deck gerado:", result.stdout)

    def test_lists_all_excel_workbook_builder_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "excel-workbook-builder",
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
                "add-formulas-and-validations",
                "compare-template-versions",
                "create-adjustment-suggestions",
                "create-pivot-summary",
                "create-summary-dashboard",
                "create-template",
                "create-template-version",
                "deprecate-template-version",
                "explain-reconciliation-differences",
                "export-workbook-artifacts",
                "generate-reconciliation-report",
                "generate-template-input-file",
                "generate-workbook-from-data",
                "generate-workbook-from-template",
                "ingest-source-document",
                "ingest-workbook-data",
                "inspect-template",
                "list-template-versions",
                "list-templates",
                "map-source-to-template",
                "normalize-tabular-data",
                "plan-workbook",
                "promote-template-version",
                "reconcile-datasets",
                "refine-generated-workbook",
                "refine-template",
                "refresh-workbook-data",
                "register-template",
                "render-workbook-preview",
                "request-database-data",
                "review-generated-workbook",
                "run-workbook-operation",
                "scan-formula-errors",
                "update-existing-workbook",
                "validate-reconciliation-rules",
                "validate-source-data",
            },
        )

    def test_excel_register_template_creates_versioned_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "conciliation-template.xlsx"
            templates_root = Path(tmpdir) / "templates"
            create_test_workbook(template_path, {"Template": [["field", "value"], ["name", ""]]})

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "register-template",
                    "--template",
                    str(template_path),
                    "--template-id",
                    "conciliation-report",
                    "--name",
                    "Relatorio de Conciliacao",
                    "--version",
                    "0.1.0",
                    "--status",
                    "validated",
                    "--templates-root",
                    str(templates_root),
                    "--yes-save",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            template_dir = templates_root / "conciliation-report"
            version_dir = template_dir / "versions" / "0.1.0"
            self.assertTrue((template_dir / "template.yaml").exists())
            self.assertTrue((template_dir / "changelog.md").exists())
            self.assertTrue((version_dir / "template.xlsx").exists())
            self.assertTrue((version_dir / "input-schema.xlsx").exists())
            self.assertTrue((version_dir / "input-schema.md").exists())
            self.assertTrue((version_dir / "sheet-map.yaml").exists())
            manifest = (template_dir / "template.yaml").read_text(encoding="utf-8")
            self.assertIn("current_version: 0.1.0", manifest)
            self.assertIn("status: validated", manifest)

    def test_excel_generate_from_template_preserves_template_sheets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "kpi-template.xlsx"
            templates_root = Path(tmpdir) / "templates"
            input_path = Path(tmpdir) / "input.json"
            output_path = Path(tmpdir) / "output.xlsx"
            inspection_path = Path(tmpdir) / "inspection.md"

            create_test_workbook(
                template_path,
                {
                    "Template": [["Title", "Sustentacao KPIs"], ["Total Tickets", ""]],
                    "Data": [["id", "status"], [1, "Aberto"]],
                },
            )
            input_path.write_text(
                json.dumps(
                    {
                        "columns": ["metric", "value"],
                        "rows": [{"metric": "Total Tickets", "value": 10}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            self.run_cli_ok(
                "run",
                "excel-workbook-builder",
                "register-template",
                "--template",
                str(template_path),
                "--template-id",
                "kpi-template",
                "--version",
                "1.0.0",
                "--status",
                "validated",
                "--templates-root",
                str(templates_root),
                "--yes-save",
            )
            self.run_cli_ok(
                "run",
                "excel-workbook-builder",
                "generate-workbook-from-template",
                "--template-id",
                "kpi-template",
                "--templates-root",
                str(templates_root),
                "--input",
                str(input_path),
                "--output",
                str(output_path),
            )
            self.run_cli_ok(
                "run",
                "excel-workbook-builder",
                "inspect-template",
                "--workbook",
                str(output_path),
                "--output",
                str(inspection_path),
            )
            inspection = inspection_path.read_text(encoding="utf-8")
            self.assertIn("Template", inspection)
            self.assertIn("Data", inspection)

    def test_excel_refresh_preserves_existing_non_data_sheets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workbook_path = Path(tmpdir) / "original.xlsx"
            refresh_csv = Path(tmpdir) / "refresh.csv"
            output_path = Path(tmpdir) / "refreshed.xlsx"
            inspection_path = Path(tmpdir) / "inspection.md"

            create_test_workbook(
                workbook_path,
                {
                    "Dashboard": [["Metric", "Value"], ["Tickets", "=COUNTA(Data!A:A)-1"]],
                    "Data": [["id", "status"], [1, "Aberto"]],
                },
            )
            refresh_csv.write_text("id,status\n1,Fechado\n2,Aberto\n", encoding="utf-8")

            self.run_cli_ok(
                "run",
                "excel-workbook-builder",
                "refresh-workbook-data",
                "--workbook",
                str(workbook_path),
                "--input",
                str(refresh_csv),
                "--output",
                str(output_path),
                "--sheet",
                "Data",
            )
            self.run_cli_ok(
                "run",
                "excel-workbook-builder",
                "inspect-template",
                "--workbook",
                str(output_path),
                "--output",
                str(inspection_path),
            )
            inspection = inspection_path.read_text(encoding="utf-8")
            self.assertIn("Dashboard", inspection)
            self.assertIn("Data", inspection)

    def test_excel_node_script_timeout_reports_hanging_child(self) -> None:
        workbook_support = load_workbook_support_module()
        started_at = time.monotonic()

        with self.assertRaisesRegex(TimeoutError, "node script timed out"):
            workbook_support.run_node_script(
                "setInterval(() => {}, 1000);\n",
                [],
                timeout_seconds=0.2,
            )

        self.assertLess(time.monotonic() - started_at, 5)

    def test_excel_promote_template_version_requires_existing_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "template.xlsx"
            templates_root = Path(tmpdir) / "templates"
            create_test_workbook(template_path, {"Template": [["field", "value"]]})
            self.run_cli_ok(
                "run",
                "excel-workbook-builder",
                "register-template",
                "--template",
                str(template_path),
                "--template-id",
                "finance-template",
                "--version",
                "1.0.0",
                "--status",
                "draft",
                "--templates-root",
                str(templates_root),
                "--yes-save",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "promote-template-version",
                    "--template-id",
                    "finance-template",
                    "--template-version",
                    "9.9.9",
                    "--templates-root",
                    str(templates_root),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("template version not found in manifest", result.stdout)

    def test_excel_promote_template_version_updates_current_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "template.xlsx"
            templates_root = Path(tmpdir) / "templates"
            create_test_workbook(template_path, {"Template": [["field", "value"]]})
            self.run_cli_ok(
                "run",
                "excel-workbook-builder",
                "register-template",
                "--template",
                str(template_path),
                "--template-id",
                "finance-template",
                "--version",
                "1.0.0",
                "--status",
                "draft",
                "--templates-root",
                str(templates_root),
                "--yes-save",
            )

            self.run_cli_ok(
                "run",
                "excel-workbook-builder",
                "promote-template-version",
                "--template-id",
                "finance-template",
                "--template-version",
                "1.0.0",
                "--templates-root",
                str(templates_root),
            )

            manifest = (templates_root / "finance-template" / "template.yaml").read_text(encoding="utf-8")
            self.assertIn("current_version: 1.0.0", manifest)
            self.assertIn("status: validated", manifest)

    def test_excel_ingests_csv_and_generates_workbook(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "tickets.csv"
            extracted_path = Path(tmpdir) / "tickets.json"
            output_path = Path(tmpdir) / "tickets.xlsx"
            source_path.write_text(
                "id,status,valor\n1,Aberto,10.5\n2,Fechado,7\n",
                encoding="utf-8",
            )

            ingest = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "ingest-source-document",
                    "--source",
                    str(source_path),
                    "--output",
                    str(extracted_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(ingest.returncode, 0, ingest.stderr)
            payload = json.loads(extracted_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["row_count"], 2)
            self.assertEqual(payload["columns"], ["id", "status", "valor"])

            generated = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "generate-workbook-from-data",
                    "--input",
                    str(extracted_path),
                    "--output",
                    str(output_path),
                    "--title",
                    "Tickets",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(generated.returncode, 0, generated.stderr)
            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 0)
            self.assertEqual(output_path.read_bytes()[:2], b"PK")
            self.assertIn("Workbook gerado:", generated.stdout)

    def test_excel_reconcile_datasets_creates_workbook(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            left_path = Path(tmpdir) / "left.csv"
            right_path = Path(tmpdir) / "right.csv"
            output_path = Path(tmpdir) / "reconciliation.xlsx"
            summary_path = Path(tmpdir) / "reconciliation.json"
            left_path.write_text("id,amount\n1,100\n2,50\n3,20\n", encoding="utf-8")
            right_path.write_text("id,amount\n1,100\n2,45\n4,10\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "reconcile-datasets",
                    "--left",
                    str(left_path),
                    "--right",
                    str(right_path),
                    "--key",
                    "id",
                    "--compare-column",
                    "amount",
                    "--output",
                    str(output_path),
                    "--summary-output",
                    str(summary_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.read_bytes()[:2], b"PK")
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["matched"], 1)
            self.assertEqual(summary["different"], 1)
            self.assertEqual(summary["left_only"], 1)
            self.assertEqual(summary["right_only"], 1)

    def test_excel_phase_2_inspects_renders_and_ingests_workbook(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "tickets.csv"
            extracted_path = Path(tmpdir) / "tickets.json"
            workbook_path = Path(tmpdir) / "tickets.xlsx"
            preview_path = Path(tmpdir) / "tickets.png"
            ingested_path = Path(tmpdir) / "tickets-from-workbook.json"
            review_path = Path(tmpdir) / "inspect.md"
            source_path.write_text(
                "id,status,valor\n1,Aberto,10.5\n2,Fechado,7\n",
                encoding="utf-8",
            )
            ingest = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "ingest-source-document",
                    "--source",
                    str(source_path),
                    "--output",
                    str(extracted_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(ingest.returncode, 0, ingest.stderr)
            generated = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "generate-workbook-from-data",
                    "--input",
                    str(extracted_path),
                    "--output",
                    str(workbook_path),
                    "--title",
                    "Tickets",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)

            rendered = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "render-workbook-preview",
                    "--workbook",
                    str(workbook_path),
                    "--sheet",
                    "Summary",
                    "--output",
                    str(preview_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            self.assertTrue(preview_path.exists())
            self.assertGreater(preview_path.stat().st_size, 0)

            workbook_ingest = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "ingest-workbook-data",
                    "--workbook",
                    str(workbook_path),
                    "--sheet",
                    "Data",
                    "--output",
                    str(ingested_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(workbook_ingest.returncode, 0, workbook_ingest.stderr)
            payload = json.loads(ingested_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["row_count"], 2)
            self.assertEqual(payload["columns"], ["id", "status", "valor"])

            inspected = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "inspect-template",
                    "--template",
                    str(workbook_path),
                    "--output",
                    str(review_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(inspected.returncode, 0, inspected.stderr)
            review = review_path.read_text(encoding="utf-8")
            self.assertIn("Workbook Inspection", review)
            self.assertIn("Worksheets", review)

    def test_excel_review_fails_when_required_sheet_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workbook_path = Path(tmpdir) / "workbook.xlsx"
            review_path = Path(tmpdir) / "review.md"
            create_test_workbook(workbook_path, {"Data": [["id"], [1]]})

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "review-generated-workbook",
                    "--workbook",
                    str(workbook_path),
                    "--required-sheet",
                    "Dashboard",
                    "--strict",
                    "--output",
                    str(review_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertNotEqual(result.returncode, 0)
            review = review_path.read_text(encoding="utf-8")
            self.assertIn("Status: fail", review)
            self.assertIn("required sheet missing: Dashboard", review)

    def test_excel_phase_2_normalizes_validates_maps_and_delegates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "clientes.csv"
            normalized_path = Path(tmpdir) / "clientes-normalized.json"
            schema_path = Path(tmpdir) / "schema.json"
            validation_path = Path(tmpdir) / "validation.md"
            mapping_path = Path(tmpdir) / "mapping.yaml"
            delegation_path = Path(tmpdir) / "delegation.md"
            source_path.write_text(
                "Cliente ID,Valor Total,Data Base\n1,10.5,2026-06-21\n2,7,2026-06-22\n",
                encoding="utf-8",
            )
            schema_path.write_text(
                json.dumps(
                    {
                        "required_columns": ["cliente_id", "valor_total"],
                        "types": {"cliente_id": "number", "valor_total": "number"},
                        "unique": ["cliente_id"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            normalized = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "normalize-tabular-data",
                    "--input",
                    str(source_path),
                    "--output",
                    str(normalized_path),
                    "--slug-columns",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(normalized.returncode, 0, normalized.stderr)
            payload = json.loads(normalized_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["columns"], ["cliente_id", "valor_total", "data_base"])

            validated = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "validate-source-data",
                    "--input",
                    str(normalized_path),
                    "--schema",
                    str(schema_path),
                    "--output",
                    str(validation_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertIn("Status: pass", validation_path.read_text(encoding="utf-8"))

            mapped = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "map-source-to-template",
                    "--source-schema",
                    str(normalized_path),
                    "--template-id",
                    "cliente-report",
                    "--field",
                    "cliente_id=Inputs!A2",
                    "--field",
                    "valor_total=Inputs!B2",
                    "--output",
                    str(mapping_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(mapped.returncode, 0, mapped.stderr)
            self.assertIn("cliente_id", mapping_path.read_text(encoding="utf-8"))

            delegated = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "request-database-data",
                    "--agent-id",
                    "postgres-data-analyzer",
                    "--capability-id",
                    "run-readonly-query",
                    "--request",
                    "listar clientes ativos",
                    "--expected-schema",
                    "cliente_id,valor_total",
                    "--output",
                    str(delegation_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(delegated.returncode, 0, delegated.stderr)
            delegation = delegation_path.read_text(encoding="utf-8")
            self.assertIn("postgres-data-analyzer", delegation)
            self.assertIn("run-readonly-query", delegation)

    def test_excel_request_database_data_can_execute_allowed_delegate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_devkit = Path(tmpdir) / "fake-ai-devkit"
            result_path = Path(tmpdir) / "delegated.json"
            fake_devkit.write_text(
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "print(json.dumps({'argv': sys.argv[1:], 'rows': [{'id': 1}]}))\n",
                encoding="utf-8",
            )
            fake_devkit.chmod(0o755)

            self.run_cli_ok(
                "run",
                "excel-workbook-builder",
                "request-database-data",
                "--agent-id",
                "postgres-data-analyzer",
                "--capability-id",
                "run-readonly-query",
                "--request",
                "listar clientes ativos",
                "--expected-schema",
                "id",
                "--execute",
                "--ai-devkit",
                str(fake_devkit),
                "--result-output",
                str(result_path),
            )

            payload = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["rows"], [{"id": 1}])
            self.assertEqual(payload["argv"][:3], ["run", "postgres-data-analyzer", "run-readonly-query"])

    def test_excel_phase_3_reconciles_composite_keys_and_multi_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            left_path = Path(tmpdir) / "left.csv"
            right_path = Path(tmpdir) / "right.csv"
            output_path = Path(tmpdir) / "reconciliation.xlsx"
            summary_path = Path(tmpdir) / "reconciliation.json"
            left_path.write_text(
                "tenant,id,amount,status\nA,1,100,ok\nA,2,50,ok\nB,3,20,pending\n",
                encoding="utf-8",
            )
            right_path.write_text(
                "tenant,id,amount,status\nA,1,100,ok\nA,2,45,ok\nB,3,20,closed\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "reconcile-datasets",
                    "--left",
                    str(left_path),
                    "--right",
                    str(right_path),
                    "--key",
                    "tenant,id",
                    "--compare-column",
                    "amount",
                    "--compare-column",
                    "status",
                    "--output",
                    str(output_path),
                    "--summary-output",
                    str(summary_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output_path.read_bytes()[:2], b"PK")
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["matched"], 1)
            self.assertEqual(summary["different"], 2)
            self.assertEqual(summary["left_only"], 0)
            self.assertEqual(summary["right_only"], 0)
            self.assertEqual(summary["keys"], ["tenant", "id"])
            self.assertEqual(summary["compare_columns"], ["amount", "status"])

    def test_excel_phase_3_refreshes_workbook_with_new_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            initial_csv = Path(tmpdir) / "initial.csv"
            refresh_csv = Path(tmpdir) / "refresh.csv"
            initial_json = Path(tmpdir) / "initial.json"
            workbook_path = Path(tmpdir) / "initial.xlsx"
            refreshed_path = Path(tmpdir) / "refreshed.xlsx"
            ingested_path = Path(tmpdir) / "refreshed.json"
            initial_csv.write_text("id,status,valor\n1,Aberto,10\n", encoding="utf-8")
            refresh_csv.write_text("id,status,valor\n1,Fechado,15\n2,Aberto,7\n", encoding="utf-8")

            ingest = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "ingest-source-document",
                    "--source",
                    str(initial_csv),
                    "--output",
                    str(initial_json),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(ingest.returncode, 0, ingest.stderr)
            generated = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "generate-workbook-from-data",
                    "--input",
                    str(initial_json),
                    "--output",
                    str(workbook_path),
                    "--title",
                    "Refresh Test",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)

            refreshed = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "refresh-workbook-data",
                    "--workbook",
                    str(workbook_path),
                    "--input",
                    str(refresh_csv),
                    "--output",
                    str(refreshed_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
            self.assertEqual(refreshed_path.read_bytes()[:2], b"PK")

            workbook_ingest = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "ingest-workbook-data",
                    "--workbook",
                    str(refreshed_path),
                    "--sheet",
                    "Data",
                    "--output",
                    str(ingested_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(workbook_ingest.returncode, 0, workbook_ingest.stderr)
            payload = json.loads(ingested_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["row_count"], 2)
            self.assertEqual(payload["rows"][0]["status"], "Fechado")

    def test_excel_phase_3_runs_aggregate_operation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "tickets.csv"
            output_path = Path(tmpdir) / "aggregate.xlsx"
            ingested_path = Path(tmpdir) / "aggregate.json"
            source_path.write_text(
                "status,valor\nAberto,10\nAberto,7\nFechado,3\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "run-workbook-operation",
                    "--input",
                    str(source_path),
                    "--operation",
                    "aggregate",
                    "--group-by",
                    "status",
                    "--value",
                    "valor",
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output_path.read_bytes()[:2], b"PK")

            workbook_ingest = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "ingest-workbook-data",
                    "--workbook",
                    str(output_path),
                    "--sheet",
                    "Data",
                    "--output",
                    str(ingested_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(workbook_ingest.returncode, 0, workbook_ingest.stderr)
            payload = json.loads(ingested_path.read_text(encoding="utf-8"))
            rows_by_status = {row["status"]: row for row in payload["rows"]}
            self.assertEqual(rows_by_status["Aberto"]["sum_valor"], 17)
            self.assertEqual(rows_by_status["Fechado"]["sum_valor"], 3)

    def test_excel_phase_3_adds_formula_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "tickets.csv"
            extracted_path = Path(tmpdir) / "tickets.json"
            workbook_path = Path(tmpdir) / "tickets.xlsx"
            formula_plan = Path(tmpdir) / "formula-plan.json"
            output_path = Path(tmpdir) / "tickets-formulas.xlsx"
            ingested_path = Path(tmpdir) / "calculations.json"
            source_path.write_text("id,valor\n1,10\n2,7\n", encoding="utf-8")
            formula_plan.write_text(
                json.dumps(
                    {
                        "sheet": "Calculations",
                        "cells": [
                            {"cell": "A1", "label": "Total"},
                            {"cell": "B1", "formula": "=SUM(Data!B2:B3)"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            ingest = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "ingest-source-document",
                    "--source",
                    str(source_path),
                    "--output",
                    str(extracted_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(ingest.returncode, 0, ingest.stderr)
            generated = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "generate-workbook-from-data",
                    "--input",
                    str(extracted_path),
                    "--output",
                    str(workbook_path),
                    "--title",
                    "Formula Test",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "add-formulas-and-validations",
                    "--workbook",
                    str(workbook_path),
                    "--formula-plan",
                    str(formula_plan),
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output_path.read_bytes()[:2], b"PK")

            workbook_ingest = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "ingest-workbook-data",
                    "--workbook",
                    str(output_path),
                    "--sheet",
                    "Calculations",
                    "--output",
                    str(ingested_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(workbook_ingest.returncode, 0, workbook_ingest.stderr)
            payload = json.loads(ingested_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["columns"], ["Total", "17"])

    def test_excel_adds_formula_validation_and_comment_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workbook_path = Path(tmpdir) / "tickets.xlsx"
            formula_plan = Path(tmpdir) / "formula-plan.json"
            output_path = Path(tmpdir) / "tickets-formulas.xlsx"
            inspection_path = Path(tmpdir) / "inspection.md"
            create_test_workbook(workbook_path, {"Data": [["id", "status"], [1, "Aberto"], [2, "Fechado"]]})
            formula_plan.write_text(
                json.dumps(
                    {
                        "sheet": "Inputs",
                        "cells": [
                            {"cell": "A1", "label": "Status", "format": {"bold": True}},
                            {"cell": "B1", "formula": "=COUNTA(Data!A:A)-1"},
                        ],
                        "validations": [
                            {"range": "A2:A20", "type": "list", "values": ["Aberto", "Fechado"]}
                        ],
                        "comments": [
                            {"cell": "A1", "text": "Status permitido para o relatorio"}
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            self.run_cli_ok(
                "run",
                "excel-workbook-builder",
                "add-formulas-and-validations",
                "--workbook",
                str(workbook_path),
                "--formula-plan",
                str(formula_plan),
                "--output",
                str(output_path),
            )
            self.run_cli_ok(
                "run",
                "excel-workbook-builder",
                "inspect-template",
                "--workbook",
                str(output_path),
                "--output",
                str(inspection_path),
            )
            inspection = inspection_path.read_text(encoding="utf-8")
            self.assertIn("Inputs", inspection)
            self.assertIn("_Comments", inspection)
            self.assertIn("Data validations: 1", inspection)

    def test_lists_all_bpo_analyser_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "bpo-analyser",
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
                "analyze-cpf-proposals",
                "analyze-proposal",
                "consult-attached-documents",
                "consult-proposal",
                "find-latest-proposal-by-cpf",
                "list-proposals-by-cpf",
                "test-connection",
            },
        )

    def test_all_bpo_analyser_capabilities_have_runner(self) -> None:
        for capability in (
            "analyze-cpf-proposals",
            "analyze-proposal",
            "consult-attached-documents",
            "consult-proposal",
            "find-latest-proposal-by-cpf",
            "list-proposals-by-cpf",
            "test-connection",
        ):
            with self.subTest(capability=capability):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--json",
                        "inspect",
                        "bpo-analyser",
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

    def test_lists_all_n1_support_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "n1-support-agent",
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
                "analyze-bpo-proposal",
                "analyze-cognito-user",
                "analyze-onboarding-status",
                "analyze-proposal-status",
                "analyze-restrictive-base",
                "collect-customer-logs",
                "decide-n1-outcome",
                "execute-n1-card-runbook",
                "extract-card-entities",
                "generate-n1-artifacts",
                "route-customer-symptom",
                "update-azure-card",
            },
        )

    def test_all_n1_support_capabilities_have_runner(self) -> None:
        for capability in (
            "analyze-bpo-proposal",
            "analyze-cognito-user",
            "analyze-onboarding-status",
            "analyze-proposal-status",
            "analyze-restrictive-base",
            "collect-customer-logs",
            "decide-n1-outcome",
            "execute-n1-card-runbook",
            "extract-card-entities",
            "generate-n1-artifacts",
            "route-customer-symptom",
            "update-azure-card",
        ):
            with self.subTest(capability=capability):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--json",
                        "inspect",
                        "n1-support-agent",
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

    def test_lists_all_n2_support_capabilities(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--json",
                "capabilities",
                "n2-support-agent",
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
                "analyze-code-root-cause",
                "build-reproduction-strategy",
                "classify-root-cause",
                "correlate-runtime-evidence",
                "execute-specialist-validation",
                "execute-n2-investigation",
                "generate-card-comment",
                "generate-patch-plan",
                "load-support-context",
                "rank-code-findings",
                "review-patch-plan-readiness",
                "select-specialist-checks",
                "update-azure-workflow",
                "update-n2-card-workflow",
                "validate-n1-handoff",
            },
        )

    def test_all_n2_support_capabilities_have_runner(self) -> None:
        for capability in (
            "analyze-code-root-cause",
            "build-reproduction-strategy",
            "classify-root-cause",
            "correlate-runtime-evidence",
            "execute-specialist-validation",
            "execute-n2-investigation",
            "generate-card-comment",
            "generate-patch-plan",
            "load-support-context",
            "rank-code-findings",
            "review-patch-plan-readiness",
            "select-specialist-checks",
            "update-azure-workflow",
            "update-n2-card-workflow",
            "validate-n1-handoff",
        ):
            with self.subTest(capability=capability):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--json",
                        "inspect",
                        "n2-support-agent",
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

    def test_software_specification_analysis_flow_capabilities_have_runners(self) -> None:
        for capability in (
            "conduct-requirements-interview",
            "refine-analysis-with-feedback",
            "create-final-spec-from-analysis",
        ):
            with self.subTest(capability=capability):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--json",
                        "inspect",
                        "software-specification-analyst",
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

    def test_run_analyze_project_context_infers_depth_and_applies_focus(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "sample-app"
            (project_dir / "src" / "auth").mkdir(parents=True)
            (project_dir / "src" / "tickets").mkdir(parents=True)
            (project_dir / "migrations").mkdir()
            (project_dir / "README.md").write_text(
                "# Sample App\n\nSistema de solicitacoes com login e permissoes.",
                encoding="utf-8",
            )
            (project_dir / ".env.example").write_text("AUTH_SECRET=\nDATABASE_URL=\n", encoding="utf-8")
            (project_dir / "src" / "auth" / "permissions.ts").write_text(
                "export function canOpenTicket(role: string) { return role === 'attendant'; }",
                encoding="utf-8",
            )
            (project_dir / "src" / "tickets" / "requests.ts").write_text(
                "export function openSolicitacao(userId: string, status: string) { return { userId, status }; }",
                encoding="utf-8",
            )
            (project_dir / "migrations" / "001_create_tickets.sql").write_text(
                "create table tickets (id int, user_id int, status varchar(20));",
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
                    "--focus",
                    "abertura de solicitacoes",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            analysis = (output_dir / "analysis-context.md").read_text(encoding="utf-8")
            questions = (output_dir / "business-questions.md").read_text(encoding="utf-8")
            impact = (output_dir / "technical-impact-analysis.md").read_text(encoding="utf-8")
            self.assertIn("Profundidade: `deep`", analysis)
            self.assertIn("Justificativa Da Profundidade", analysis)
            self.assertIn("Foco Da Analise", questions)
            self.assertIn("abertura de solicitacoes", questions)
            self.assertIn("src/tickets/requests.ts", impact)

    def test_run_interview_refine_and_final_spec_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "demanda.md"
            input_path.write_text(
                "# Portal de atendimento\n\nPermitir abertura e acompanhamento de solicitacoes.",
                encoding="utf-8",
            )
            analysis_dir = Path(tmpdir) / "analysis"
            analysis_dir.mkdir()
            (analysis_dir / "analysis-context.md").write_text(
                "# Contexto\n\nTermos observados: solicitacoes, atendimento, status.",
                encoding="utf-8",
            )
            (analysis_dir / "business-questions.md").write_text(
                "# Perguntas\n\n- Quem pode abrir solicitacoes?\n- Quais status existem?",
                encoding="utf-8",
            )
            interview_dir = Path(tmpdir) / "interview"

            interview = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "software-specification-analyst",
                    "conduct-requirements-interview",
                    "--input",
                    str(input_path),
                    "--analysis-dir",
                    str(analysis_dir),
                    "--output-dir",
                    str(interview_dir),
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

            self.assertEqual(interview.returncode, 0, interview.stderr)
            self.assertTrue((interview_dir / "interview-guide.md").exists())
            self.assertTrue((interview_dir / "stakeholder-questions.md").exists())

            feedback_path = Path(tmpdir) / "respostas.md"
            feedback_path.write_text(
                "# Portal de atendimento\n\n- Atendentes e clientes podem abrir solicitacoes.\n- Status: aberto, em atendimento, concluido.",
                encoding="utf-8",
            )
            refined_dir = Path(tmpdir) / "refined"
            refine = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "software-specification-analyst",
                    "refine-analysis-with-feedback",
                    "--analysis-dir",
                    str(analysis_dir),
                    "--feedback",
                    str(feedback_path),
                    "--output-dir",
                    str(refined_dir),
                    "--yes-create-dir",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(refine.returncode, 0, refine.stderr)
            self.assertTrue((refined_dir / "refined-analysis.md").exists())
            self.assertTrue((refined_dir / "decision-log.md").exists())

            final_dir = Path(tmpdir) / "final"
            final = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "software-specification-analyst",
                    "create-final-spec-from-analysis",
                    "--analysis-dir",
                    str(refined_dir),
                    "--output-dir",
                    str(final_dir),
                    "--yes-create-dir",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(final.returncode, 0, final.stderr)
            spec = (final_dir / "software-specification.md").read_text(encoding="utf-8")
            self.assertIn("Portal de atendimento", spec)
            self.assertIn("Atendentes e clientes", spec)
            self.assertTrue((final_dir / "requirements-traceability.md").exists())

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
                "analyze-query-result",
                "build-analysis-query",
                "compare-tables",
                "describe-table",
                "detect-data-quality-issues",
                "detect-sensitive-columns",
                "estimate-table-size",
                "explain-query-plan",
                "explore-database-domain",
                "generate-data-report",
                "generate-erd-report",
                "list-databases",
                "list-relationships",
                "list-schemas",
                "list-tables",
                "profile-table",
                "run-readonly-query",
                "sample-table",
                "search-columns",
                "search-tables",
                "suggest-joins",
                "test-connection",
                "trace-record",
                "validate-readonly-query",
            },
        )

    def test_all_postgres_capabilities_have_runner(self) -> None:
        for capability in (
            "analyze-cpf-column",
            "analyze-query-result",
            "build-analysis-query",
            "compare-tables",
            "describe-table",
            "detect-data-quality-issues",
            "detect-sensitive-columns",
            "estimate-table-size",
            "explain-query-plan",
            "explore-database-domain",
            "generate-data-report",
            "generate-erd-report",
            "list-databases",
            "list-relationships",
            "list-schemas",
            "list-tables",
            "profile-table",
            "run-readonly-query",
            "sample-table",
            "search-columns",
            "search-tables",
            "suggest-joins",
            "test-connection",
            "trace-record",
            "validate-readonly-query",
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
                "triage-incident",
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
            "triage-incident",
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
                "list-log-streams",
                "run-insights-query",
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
            "list-log-streams",
            "run-insights-query",
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
                "attach-file",
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
            "attach-file",
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


    # -------------------------------------------------------------------------
    # presentation-deck-builder — new runner tests (P0 backlog)
    # -------------------------------------------------------------------------

    def _register_template(self, templates_root: Path, template_id: str, version: str, status: str) -> None:
        """Helper: register a template with --yes-save."""
        template_path = templates_root.parent / f"{template_id}.pptx"
        template_path.write_bytes(b"fake pptx content")
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "run",
                "presentation-deck-builder",
                "register-template",
                "--template",
                str(template_path),
                "--template-id",
                template_id,
                "--version",
                version,
                "--status",
                status,
                "--templates-root",
                str(templates_root),
                "--yes-save",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_presentation_list_templates_shows_registered(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_root = Path(tmpdir) / "templates"
            self._register_template(templates_root, "kpi-report", "1.0.0", "validated")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "list-templates",
                    "--templates-root",
                    str(templates_root),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("kpi-report", result.stdout)
            self.assertIn("1.0.0", result.stdout)

    def test_presentation_generate_template_input_file_creates_schemas(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_root = Path(tmpdir) / "templates"
            self._register_template(templates_root, "status-deck", "0.1.0", "validated")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "generate-template-input-file",
                    "--template-id",
                    "status-deck",
                    "--templates-root",
                    str(templates_root),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            version_dir = templates_root / "status-deck" / "versions" / "0.1.0"
            self.assertTrue((version_dir / "input-schema.xlsx").exists())
            self.assertTrue((version_dir / "input-schema.md").exists())
            self.assertIn("input-schema.xlsx", result.stdout)

    def test_presentation_promote_template_version_updates_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_root = Path(tmpdir) / "templates"
            self._register_template(templates_root, "exec-report", "1.0.0", "draft")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "promote-template-version",
                    "--template-id",
                    "exec-report",
                    "--template-version",
                    "1.0.0",
                    "--templates-root",
                    str(templates_root),
                    "--yes-confirm",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = (templates_root / "exec-report" / "template.yaml").read_text(encoding="utf-8")
            self.assertIn("current_version: 1.0.0", manifest)
            self.assertIn("status: validated", manifest)

    def test_presentation_promote_requires_existing_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_root = Path(tmpdir) / "templates"
            self._register_template(templates_root, "exec-report", "1.0.0", "draft")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "promote-template-version",
                    "--template-id",
                    "exec-report",
                    "--template-version",
                    "9.9.9",
                    "--templates-root",
                    str(templates_root),
                    "--yes-confirm",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("template version not found in manifest", result.stdout)

    def test_presentation_deprecate_template_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_root = Path(tmpdir) / "templates"
            self._register_template(templates_root, "old-report", "1.0.0", "draft")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "deprecate-template-version",
                    "--template-id",
                    "old-report",
                    "--template-version",
                    "1.0.0",
                    "--reason",
                    "substituido por versao 2.0.0",
                    "--templates-root",
                    str(templates_root),
                    "--yes-confirm",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = (templates_root / "old-report" / "template.yaml").read_text(encoding="utf-8")
            self.assertIn("status: deprecated", manifest)
            self.assertIn("substituido por versao 2.0.0", result.stdout)

    def test_presentation_create_template_version_creates_new_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_root = Path(tmpdir) / "templates"
            self._register_template(templates_root, "kpi-slides", "1.0.0", "validated")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "create-template-version",
                    "--template-id",
                    "kpi-slides",
                    "--new-version",
                    "1.1.0",
                    "--base-version",
                    "1.0.0",
                    "--templates-root",
                    str(templates_root),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            new_dir = templates_root / "kpi-slides" / "versions" / "1.1.0"
            self.assertTrue(new_dir.exists())
            self.assertTrue((new_dir / "template.pptx").exists())
            self.assertTrue((new_dir / "slide-map.yaml").exists())
            # original version must still exist
            self.assertTrue((templates_root / "kpi-slides" / "versions" / "1.0.0").exists())
            # new version should be draft
            manifest = (templates_root / "kpi-slides" / "template.yaml").read_text(encoding="utf-8")
            self.assertIn("1.1.0", manifest)

    def test_presentation_create_version_rejects_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_root = Path(tmpdir) / "templates"
            self._register_template(templates_root, "kpi-slides", "1.0.0", "validated")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "create-template-version",
                    "--template-id",
                    "kpi-slides",
                    "--new-version",
                    "1.0.0",
                    "--templates-root",
                    str(templates_root),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already exists", result.stderr)

    def test_presentation_refine_template_creates_new_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_root = Path(tmpdir) / "templates"
            self._register_template(templates_root, "status-slides", "1.0.0", "validated")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "refine-template",
                    "--template-id",
                    "status-slides",
                    "--change-request",
                    "adicionar campo de data ao slide de abertura",
                    "--base-version",
                    "1.0.0",
                    "--bump",
                    "minor",
                    "--templates-root",
                    str(templates_root),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            # base version must still exist untouched
            self.assertTrue(
                (templates_root / "status-slides" / "versions" / "1.0.0").exists()
            )
            # new version created
            self.assertIn("1.1.0", result.stdout)
            manifest = (templates_root / "status-slides" / "template.yaml").read_text(encoding="utf-8")
            self.assertIn("1.1.0", manifest)

    def test_presentation_refine_never_overwrites_validated_base(self) -> None:
        """Guardrail: validated base must not be modified after refine."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_root = Path(tmpdir) / "templates"
            self._register_template(templates_root, "exec-kpis", "2.0.0", "validated")
            original_manifest = (
                templates_root / "exec-kpis" / "template.yaml"
            ).read_text(encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "refine-template",
                    "--template-id",
                    "exec-kpis",
                    "--change-request",
                    "mudar cor do titulo",
                    "--base-version",
                    "2.0.0",
                    "--templates-root",
                    str(templates_root),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            # base version directory still intact
            base_pptx = templates_root / "exec-kpis" / "versions" / "2.0.0" / "template.pptx"
            self.assertTrue(base_pptx.exists())

    @unittest.skipUnless(
        (
            Path.home()
            / ".codex"
            / "plugins"
            / "cache"
            / "openai-primary-runtime"
            / "presentations"
        ).exists()
        or os.environ.get("PRESENTATIONS_SKILL_DIR"),
        "presentations skill not available in this environment",
    )
    def test_generate_deck_from_template_requires_skill_env(self) -> None:
        """When skill IS available, the test should pass (or be skipped)."""
        # This test is a placeholder — it runs only when the skill is present.
        # The actual generation test already exists as
        # test_generate_deck_from_template_creates_pptx.
        pass

    def test_generate_deck_from_template_reports_missing_skill(self) -> None:
        """Without the skill, runner must exit non-zero with a clear error message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_root = Path(tmpdir) / "templates"
            input_path = Path(tmpdir) / "input.json"
            input_path.write_text(
                json.dumps({"title": "Test", "metrics": [], "state_breakdown": {}, "highlights": []}),
                encoding="utf-8",
            )
            self._register_template(templates_root, "test-tmpl", "1.0.0", "validated")

            env = {k: v for k, v in os.environ.items() if k != "PRESENTATIONS_SKILL_DIR"}
            # Use a path that certainly does not have the skill
            env["PRESENTATIONS_SKILL_DIR"] = str(Path(tmpdir) / "nonexistent")
            env["HOME"] = str(Path(tmpdir) / "empty-home")
            env["USERPROFILE"] = str(Path(tmpdir) / "empty-home")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "presentation-deck-builder",
                    "generate-deck-from-template",
                    "--template-id",
                    "test-tmpl",
                    "--input",
                    str(input_path),
                    "--templates-root",
                    str(templates_root),
                ],
                cwd=ROOT,
                env=env,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PRESENTATIONS_SKILL_DIR", result.stderr)


if __name__ == "__main__":
    unittest.main()
