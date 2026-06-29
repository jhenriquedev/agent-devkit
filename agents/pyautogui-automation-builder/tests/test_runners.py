#!/usr/bin/env python3
"""Tests for the PyAutoGUI Automation Builder runners."""

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
AGENT_DIR = ROOT / "agents" / "pyautogui-automation-builder"
REPOSITORY_PATH = (
    AGENT_DIR
    / "infra"
    / "integrations"
    / "pyautogui-automation"
    / "pyautogui_automation_repository.py"
)


def load_repository_module():
    spec = importlib.util.spec_from_file_location("pyautogui_automation_repository", REPOSITORY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load repository from {REPOSITORY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PyAutoGUIAutomationBuilderRunnersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_module = load_repository_module()

    def write_spec(
        self,
        root: Path,
        *,
        automation_name: str = "Desktop Report Export",
        target_project: Path | None = None,
        safer_alternatives_checked: list[str] | None = None,
        purpose: str = "Export a report from a desktop-only legacy app.",
        side_effects: str = "navigation",
        user_accepts_visual_risk: str = "true",
        coordinates_policy: str = "window-relative",
        absolute_coordinate_justification: str = "",
    ) -> Path:
        path = root / "pyautogui-spec.yaml"
        target_project_line = f"target_project: {target_project}\n" if target_project else ""
        alternatives = ["checked-none-available"] if safer_alternatives_checked is None else safer_alternatives_checked
        alternatives_block = (
            "safer_alternatives_checked: []"
            if not alternatives
            else "safer_alternatives_checked:\n" + "\n".join(f"  - {item}" for item in alternatives)
        )
        absolute_line = (
            f"absolute_coordinate_justification: {absolute_coordinate_justification}\n"
            if absolute_coordinate_justification
            else ""
        )
        path.write_text(
            f"""
automation_name: {automation_name}
{target_project_line}purpose: {purpose}
target_app: Legacy Reports
target_window: Reports - Production Mirror
platform: macos
side_effects: {side_effects}
coordinates_policy: {coordinates_policy}
user_accepts_visual_risk: {user_accepts_visual_risk}
{absolute_line}{alternatives_block}
steps:
  - focus export menu
  - choose csv format
  - wait for confirmation banner
screen_preconditions:
  - Reports window is active
  - Export button is visible
verification_strategy: compare before and after screenshots and verify confirmation banner
quality_gates:
  - dry-run reviewed
  - target window confirmed
""".lstrip(),
            encoding="utf-8",
        )
        return path

    def test_plan_desktop_automation_returns_plan_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)

            result = repository.plan_desktop_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["automation"]["slug"], "desktop-report-export")
            self.assertEqual(result["write_policy"], "read_only")
            self.assertEqual(result["coordinates_policy"], "window-relative")
            planned_paths = {item["path"] for item in result["planned_artifacts"]}
            self.assertIn("pyautogui_automation.py", planned_paths)
            self.assertFalse((root / "pyautogui_automation.py").exists())

    def test_plan_desktop_automation_reports_needs_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = root / "pyautogui-spec.yaml"
            spec_path.write_text("automation_name: incomplete\n", encoding="utf-8")
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)

            result = repository.plan_desktop_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "needs-input")
            self.assertGreaterEqual(
                set(result["missing_fields"]),
                {
                    "purpose",
                    "target_app",
                    "target_window",
                    "platform",
                    "steps",
                    "screen_preconditions",
                    "verification_strategy",
                    "safer_alternatives_checked",
                    "user_accepts_visual_risk",
                    "side_effects",
                    "coordinates_policy",
                },
            )

    def test_plan_requires_safer_alternatives_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, safer_alternatives_checked=[])
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)

            result = repository.plan_desktop_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "needs-safer-alternative-review")
            self.assertEqual(result["reason"], "safer_alternatives_not_checked")

    def test_plan_blocks_when_api_or_cli_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, safer_alternatives_checked=["api", "cli"])
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)

            result = repository.plan_desktop_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "needs-safer-alternative-review")
            self.assertEqual(result["reason"], "safer_alternative_available")
            self.assertEqual(result["available_alternatives"], ["api", "cli"])

    def test_plan_requires_visual_risk_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, user_accepts_visual_risk="false")
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)

            result = repository.plan_desktop_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "needs-input")
            self.assertIn("user_accepts_visual_risk", result["missing_fields"])

    def test_plan_blocks_destructive_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, side_effects="destructive")
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)

            result = repository.plan_desktop_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "destructive_desktop_automation_blocked")

    def test_plan_blocks_secret_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, purpose="Export with PASSWORD=abc in the UI.")
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)

            result = repository.plan_desktop_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "forbidden_sensitive_marker")

    def test_plan_blocks_absolute_coordinates_without_justification(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, coordinates_policy="absolute-last-resort")
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)

            result = repository.plan_desktop_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "absolute_coordinates_need_justification")

    def test_generate_pyautogui_script_contains_required_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)

            result = repository.generate_pyautogui_script(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            content = result["content"]
            self.assertIn("pyautogui.FAILSAFE = True", content)
            self.assertIn("--dry-run", content)
            self.assertIn("--execute", content)
            self.assertIn("--confirm", content)
            self.assertIn("--screenshot-dir", content)
            self.assertIn("--abort-file", content)
            self.assertIn("before.png", content)
            self.assertIn("after.png", content)
            self.assertIn("error.png", content)
            py_compile.compile(str(self.write_temp_script(root, content)), doraise=True)

    def test_generated_script_dry_run_runs_without_pyautogui_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)
            script = self.write_temp_script(root, repository.generate_pyautogui_script(spec_path=spec_path)["content"])

            result = subprocess.run(
                [sys.executable, str(script), "--dry-run"],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["plan"]["automation"], "desktop-report-export")

    def test_generate_pyautogui_project_files_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)

            result = repository.generate_pyautogui_project_files(spec_path=spec_path)

            self.assertEqual(result["status"], "planned")
            self.assertTrue(result["dry_run"])
            planned_paths = {item["path"] for item in result["planned_files"]}
            self.assertGreaterEqual(
                planned_paths,
                {
                    "desktop-report-export/pyautogui_automation.py",
                    "desktop-report-export/README.md",
                    "desktop-report-export/tests/test_pyautogui_automation.py",
                },
            )
            self.assertFalse((target_project / "desktop-report-export").exists())

    def test_generate_pyautogui_project_files_execute_writes_inside_target_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)

            result = repository.generate_pyautogui_project_files(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "written")
            self.assertTrue((target_project / "desktop-report-export" / "pyautogui_automation.py").exists())
            for item in result["written_files"]:
                path = Path(item["path"]).resolve()
                self.assertTrue(path.is_relative_to(target_project.resolve()), item["path"])

    def test_generate_pyautogui_project_files_blocks_overwrite_without_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)
            repository.generate_pyautogui_project_files(spec_path=spec_path, execute=True)

            result = repository.generate_pyautogui_project_files(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "target_exists")

    def test_review_pyautogui_script_detects_missing_failsafe(self) -> None:
        repository = self.repository_module.PyAutoGUIAutomationRepository(root=ROOT)

        result = repository.review_pyautogui_script(text="import pyautogui\npyautogui.click(10, 10)")

        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "failed")
        self.assertTrue(any("failsafe" in finding.lower() for finding in result["findings"]))

    def test_review_pyautogui_script_accepts_generated_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)
            script = repository.generate_pyautogui_script(spec_path=spec_path)["content"]

            result = repository.review_pyautogui_script(text=script, side_effects="navigation")

            self.assertTrue(result["valid"], result["findings"])
            self.assertEqual(result["findings"], [])

    def test_wrap_pyautogui_as_capability_execute_writes_compilable_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.PyAutoGUIAutomationRepository(root=root)

            result = repository.wrap_pyautogui_as_capability(
                spec_path=spec_path,
                agent_id="desktop-ops-agent",
                capability_id="desktop-report-export",
                execute=True,
            )

            self.assertEqual(result["status"], "written")
            runner = target_project / "agents" / "desktop-ops-agent" / "capabilities" / "desktop-report-export" / "runner.py"
            self.assertTrue(runner.exists())
            py_compile.compile(str(runner), doraise=True)

    def test_plan_desktop_automation_runner_is_executable_through_agent_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = self.write_spec(Path(tmpdir))

            result = subprocess.run(
                [
                    sys.executable,
                    str(AGENT),
                    "--json",
                    "run",
                    "pyautogui-automation-builder",
                    "plan-desktop-automation",
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
        self.assertEqual(runner_payload["automation"]["slug"], "desktop-report-export")

    def write_temp_script(self, root: Path, content: str) -> Path:
        script = root / "pyautogui_automation.py"
        script.write_text(content, encoding="utf-8")
        return script


if __name__ == "__main__":
    unittest.main()
