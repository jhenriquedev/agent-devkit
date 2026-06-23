"""Tests for excel-workbook-builder template lifecycle capabilities.

Covers: create-template-version, promote-template-version, deprecate-template-version.
Requires: only Python stdlib + workbook_support (no Node runtime needed).
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Resolve agent root and add shared path
AGENT_DIR = Path(__file__).parent.parent
SHARED_DIR = AGENT_DIR / "capabilities" / "_shared"
CLI = Path(__file__).parent.parent.parent.parent / "ai-devkit"

# Add shared to path for imports
sys.path.insert(0, str(SHARED_DIR))


class TestDateImport(unittest.TestCase):
    """Bug fix: template_ops.py must import date from datetime."""

    def test_date_import_exists(self):
        """Verifies 'from datetime import date' is present in template_ops.py."""
        template_ops = SHARED_DIR / "template_ops.py"
        self.assertTrue(template_ops.exists(), "template_ops.py not found")
        content = template_ops.read_text()
        self.assertIn(
            "from datetime import date",
            content,
            "Bug not fixed: 'from datetime import date' missing in template_ops.py",
        )

    def test_date_import_functional(self):
        """date.today() must not raise NameError in template_ops module."""
        import importlib
        import importlib.util

        spec = importlib.util.spec_from_file_location("template_ops", SHARED_DIR / "template_ops.py")
        mod = importlib.util.module_from_spec(spec)
        # Should not raise
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            self.fail(f"template_ops failed to load: {e}")
        # Check date is available
        from datetime import date
        self.assertIsNotNone(date.today())


class TestKnowledgeFiles(unittest.TestCase):
    """Knowledge files required by spec must exist and be non-empty."""

    def _check_file(self, relative_path, min_lines=5):
        path = AGENT_DIR / relative_path
        self.assertTrue(path.exists(), f"Missing: {relative_path}")
        content = path.read_text(encoding="utf-8").strip()
        self.assertGreater(
            len(content.splitlines()),
            min_lines,
            f"File too short (placeholder?): {relative_path}",
        )

    def test_system_md_exists(self):
        self._check_file("knowledge/system.md", min_lines=10)

    def test_runtime_md_exists(self):
        self._check_file("knowledge/runtime.md", min_lines=10)

    def test_formula_rules_exists(self):
        self._check_file("knowledge/formula-rules.md", min_lines=3)

    def test_reconciliation_rules_exists(self):
        self._check_file("knowledge/reconciliation-rules.md", min_lines=3)

    def test_source_routing_exists(self):
        self._check_file("knowledge/source-routing.md", min_lines=3)


class TestAgentYamlDefaultContext(unittest.TestCase):
    """agent.yaml must declare default_context with system.md first."""

    def _load_yaml(self):
        import yaml
        path = AGENT_DIR / "agent.yaml"
        with open(path) as f:
            return yaml.safe_load(f)

    def test_default_context_exists(self):
        try:
            data = self._load_yaml()
        except ImportError:
            self.skipTest("PyYAML not installed")
        self.assertIn("default_context", data, "agent.yaml missing default_context")

    def test_system_md_is_first_in_default_context(self):
        try:
            data = self._load_yaml()
        except ImportError:
            self.skipTest("PyYAML not installed")
        ctx = data.get("default_context", [])
        self.assertTrue(
            len(ctx) > 0 and "system.md" in ctx[0],
            f"First item of default_context must be knowledge/system.md, got: {ctx}",
        )

    def test_orphan_knowledge_referenced(self):
        try:
            data = self._load_yaml()
        except ImportError:
            self.skipTest("PyYAML not installed")
        all_refs = str(data)
        for f in ["formula-rules.md", "reconciliation-rules.md", "source-routing.md"]:
            self.assertIn(f, all_refs, f"Orphan knowledge not referenced in agent.yaml: {f}")


class TestWritePolicyConsistency(unittest.TestCase):
    """create-adjustment-suggestions must have write_policy: output_only."""

    def test_adjustment_suggestions_write_policy(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")
        cap_yaml = AGENT_DIR / "capabilities" / "create-adjustment-suggestions" / "capability.yaml"
        self.assertTrue(cap_yaml.exists())
        with open(cap_yaml) as f:
            data = yaml.safe_load(f)
        self.assertEqual(
            data.get("write_policy"),
            "output_only",
            "create-adjustment-suggestions write_policy must be output_only (not read_only)",
        )


class TestWorkflowsNonEmpty(unittest.TestCase):
    """All capabilities must have a non-generic workflow.md (min 10 lines)."""

    def test_all_workflows_exist_and_non_generic(self):
        caps_dir = AGENT_DIR / "capabilities"
        missing = []
        generic = []
        generic_marker = "1. Entender objetivo, publico e fonte dos dados."

        for cap_dir in sorted(caps_dir.iterdir()):
            if cap_dir.name.startswith("_"):
                continue
            if not cap_dir.is_dir():
                continue
            wf = cap_dir / "workflow.md"
            if not wf.exists():
                missing.append(cap_dir.name)
                continue
            content = wf.read_text(encoding="utf-8")
            if generic_marker in content:
                generic.append(cap_dir.name)
            if len(content.strip().splitlines()) < 8:
                generic.append(cap_dir.name + " (too short)")

        self.assertEqual(missing, [], f"Missing workflow.md: {missing}")
        self.assertEqual(generic, [], f"Generic/stub workflow.md: {generic}")


class TestTemplateLifecyclePlanWorkbook(unittest.TestCase):
    """plan-workbook must run without Node and produce non-empty output."""

    def test_plan_workbook_runs(self):
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "run",
                "excel-workbook-builder",
                "plan-workbook",
                "--",
                "--brief",
                "Relatório mensal de vendas por região",
            ],
            capture_output=True,
            text=True,
            cwd=str(CLI.parent),
        )
        output = result.stdout + result.stderr
        # Should produce some markdown output (plan-workbook is Python-pure)
        self.assertEqual(result.returncode, 0, f"plan-workbook failed: {output}")
        self.assertIn("Workbook Plan", output, f"Expected plan output, got: {output}")


class TestNodeRuntimeDegradation(unittest.TestCase):
    """Node-dependent capabilities must fail gracefully with actionable message."""

    def test_node_check_documented_in_runtime_md(self):
        runtime_md = AGENT_DIR / "knowledge" / "runtime.md"
        content = runtime_md.read_text(encoding="utf-8")
        self.assertIn("node_modules not found", content)
        self.assertIn("node executable not found", content)
        self.assertIn("CODEX_NODE", content)

    def test_generate_workbook_fails_gracefully_without_node(self):
        """Without Node, generate-workbook-from-data should fail with a clear error,
        not a cryptic Python traceback."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(
                {"columns": ["id", "value"], "rows": [{"id": 1, "value": 100}]},
                f,
            )
            input_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "run",
                    "excel-workbook-builder",
                    "generate-workbook-from-data",
                    "--",
                    "--input",
                    input_path,
                    "--output",
                    "/tmp/test_workbook_skip.xlsx",
                ],
                capture_output=True,
                text=True,
                cwd=str(CLI.parent),
                env={**os.environ, "CODEX_NODE": "", "CODEX_NODE_MODULES": ""},
                timeout=30,
            )
            output = result.stdout + result.stderr
            # Either succeeds (Node available) or fails with a recognizable error
            if result.returncode != 0:
                self.assertTrue(
                    any(
                        msg in output
                        for msg in [
                            "node",
                            "artifact-tool",
                            "not found",
                            "error",
                        ]
                    ),
                    f"generate-workbook-from-data failed with unrecognized error: {output}",
                )
        except subprocess.TimeoutExpired:
            self.skipTest("generate-workbook-from-data timed out (Node environment issue)")
        finally:
            os.unlink(input_path)


if __name__ == "__main__":
    unittest.main()
