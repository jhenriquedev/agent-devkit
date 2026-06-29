#!/usr/bin/env python3
"""Tests for the Python Automation Builder runners."""

from __future__ import annotations

import importlib.util
import json
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "agent"
AGENT_DIR = ROOT / "agents" / "python-automation-builder"
REPOSITORY_PATH = AGENT_DIR / "infra" / "integrations" / "python-automation" / "python_automation_repository.py"


def load_repository_module():
    spec = importlib.util.spec_from_file_location("python_automation_repository", REPOSITORY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load repository from {REPOSITORY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PythonAutomationBuilderRunnersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_module = load_repository_module()

    def write_spec(
        self,
        root: Path,
        *,
        automation_name: str = "Report Cleanup",
        target_project: Path | None = None,
        dependencies: list[str] | None = None,
        side_effects: str = "updates-local",
        purpose: str = "Clean old generated reports and summarize the affected files.",
        systems: str = "local filesystem",
    ) -> Path:
        path = root / "automation-spec.yaml"
        target_project_line = f"target_project: {target_project}\n" if target_project else ""
        dependency_lines = "\n".join(f"  - {item}" for item in (dependencies or []))
        if not dependency_lines:
            dependency_lines = "  - pathlib"
        path.write_text(
            f"""
automation_name: {automation_name}
{target_project_line}purpose: {purpose}
inputs:
  - reports_dir
outputs:
  - summary_json
systems:
  - {systems}
frequency: daily
risk: medium
target_environment: local workstation
side_effects: {side_effects}
dependencies:
{dependency_lines}
quality_gates:
  - dry-run lists affected paths
  - exit codes are predictable
""".lstrip(),
            encoding="utf-8",
        )
        return path

    def test_plan_python_automation_returns_plan_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.PythonAutomationRepository(root=root)

            result = repository.plan_python_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["automation"]["slug"], "report-cleanup")
            self.assertEqual(result["idempotency"], "updates-local")
            self.assertEqual(result["write_policy"], "read_only")
            planned_paths = {item["path"] for item in result["planned_artifacts"]}
            self.assertIn("automation.py", planned_paths)
            self.assertFalse((root / "automation.py").exists())

    def test_plan_python_automation_reports_needs_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = root / "automation-spec.yaml"
            spec_path.write_text("automation_name: incomplete\n", encoding="utf-8")
            repository = self.repository_module.PythonAutomationRepository(root=root)

            result = repository.plan_python_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "needs-input")
            self.assertGreaterEqual(
                set(result["missing_fields"]),
                {"purpose", "inputs", "outputs", "systems", "side_effects"},
            )

    def test_plan_blocks_secret_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, purpose="Use API_KEY=abc to call the service.")
            repository = self.repository_module.PythonAutomationRepository(root=root)

            result = repository.plan_python_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "forbidden_sensitive_marker")

    def test_plan_routes_browser_desktop_dependencies_out_of_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, dependencies=["selenium"])
            repository = self.repository_module.PythonAutomationRepository(root=root)

            result = repository.plan_python_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "out_of_scope_dependency")
            self.assertIn("problem 16", " ".join(result["next_steps"]).lower())

    def test_generate_python_automation_returns_script_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.PythonAutomationRepository(root=root)

            result = repository.generate_python_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            content = result["content"]
            self.assertIn("argparse", content)
            self.assertIn("--dry-run", content)
            self.assertIn("--execute", content)
            self.assertIn("--yes", content)
            self.assertIn("redact", content)
            self.assertIn("return 0", content)
            self.assertFalse((root / "automation.py").exists())

    def test_generate_automation_project_files_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.PythonAutomationRepository(root=root)

            result = repository.generate_automation_project_files(spec_path=spec_path)

            self.assertEqual(result["status"], "planned")
            self.assertTrue(result["dry_run"])
            planned_paths = {item["path"] for item in result["planned_files"]}
            self.assertGreaterEqual(
                planned_paths,
                {
                    "report-cleanup/automation.py",
                    "report-cleanup/README.md",
                    "report-cleanup/tests/test_automation.py",
                },
            )
            self.assertFalse((target_project / "report-cleanup").exists())

    def test_generate_automation_project_files_execute_writes_inside_target_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.PythonAutomationRepository(root=root)

            result = repository.generate_automation_project_files(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "written")
            self.assertTrue((target_project / "report-cleanup" / "automation.py").exists())
            for item in result["written_files"]:
                path = Path(item["path"]).resolve()
                self.assertTrue(path.is_relative_to(target_project.resolve()), item["path"])

    def test_generate_automation_project_files_blocks_overwrite_without_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.PythonAutomationRepository(root=root)
            repository.generate_automation_project_files(spec_path=spec_path, execute=True)

            result = repository.generate_automation_project_files(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "target_exists")

    def test_review_python_automation_detects_missing_dry_run(self) -> None:
        repository = self.repository_module.PythonAutomationRepository(root=ROOT)

        result = repository.review_python_automation(text="print('hello')", side_effects="updates-local")

        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "failed")
        self.assertTrue(any("dry-run" in finding.lower() for finding in result["findings"]))

    def test_review_python_automation_accepts_generated_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.PythonAutomationRepository(root=root)
            script = repository.generate_python_automation(spec_path=spec_path)["content"]

            result = repository.review_python_automation(text=script, side_effects="updates-local")

            self.assertTrue(result["valid"], result["findings"])
            self.assertEqual(result["findings"], [])

    def test_wrap_automation_as_capability_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.PythonAutomationRepository(root=root)

            result = repository.wrap_automation_as_capability(
                spec_path=spec_path,
                agent_id="operations-agent",
                capability_id="report-cleanup",
            )

            self.assertEqual(result["status"], "planned")
            self.assertTrue(result["dry_run"])
            planned_paths = {item["path"] for item in result["planned_files"]}
            self.assertIn("agents/operations-agent/capabilities/report-cleanup/runner.py", planned_paths)
            self.assertFalse((target_project / "agents").exists())

    def test_wrap_automation_as_capability_execute_writes_compilable_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.PythonAutomationRepository(root=root)

            result = repository.wrap_automation_as_capability(
                spec_path=spec_path,
                agent_id="operations-agent",
                capability_id="report-cleanup",
                execute=True,
            )

            self.assertEqual(result["status"], "written")
            runner = target_project / "agents" / "operations-agent" / "capabilities" / "report-cleanup" / "runner.py"
            self.assertTrue(runner.exists())
            py_compile.compile(str(runner), doraise=True)

    def test_plan_python_automation_runner_is_executable_through_agent_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = self.write_spec(Path(tmpdir))

            result = subprocess.run(
                [
                    sys.executable,
                    str(AGENT),
                    "--json",
                    "run",
                    "python-automation-builder",
                    "plan-python-automation",
                    "--spec",
                    str(spec_path),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        runner_payload = json.loads(payload["stdout"])
        self.assertEqual(runner_payload["status"], "ok")
        self.assertEqual(runner_payload["automation"]["slug"], "report-cleanup")


if __name__ == "__main__":
    unittest.main()
