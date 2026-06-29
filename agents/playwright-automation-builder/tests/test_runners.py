#!/usr/bin/env python3
"""Tests for the Playwright Automation Builder runners."""

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
AGENT_DIR = ROOT / "agents" / "playwright-automation-builder"
REPOSITORY_PATH = AGENT_DIR / "infra" / "integrations" / "playwright-automation" / "playwright_automation_repository.py"


def load_repository_module():
    spec = importlib.util.spec_from_file_location("playwright_automation_repository", REPOSITORY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load repository from {REPOSITORY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PlaywrightAutomationBuilderRunnersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_module = load_repository_module()

    def write_spec(
        self,
        root: Path,
        *,
        automation_name: str = "Login Smoke Check",
        target_project: Path | None = None,
        side_effects: str = "read-only",
        selector_kind: str = "role",
        purpose: str = "Validate that a login page renders a submit button.",
    ) -> Path:
        path = root / "playwright-spec.yaml"
        target_project_line = f"target_project: {target_project}\n" if target_project else ""
        path.write_text(
            f"""
automation_name: {automation_name}
{target_project_line}purpose: {purpose}
target_url: https://example.test/login
browser: chromium
auth_strategy: none
side_effects: {side_effects}
selectors:
  - name: submit
    kind: {selector_kind}
    value: button
    name_value: Entrar
steps:
  - open target_url
  - assert submit visible
assertions:
  - submit visible
artifacts:
  - screenshot
  - trace
  - report
quality_gates:
  - stable selectors are used
""".lstrip(),
            encoding="utf-8",
        )
        return path

    def test_plan_playwright_automation_returns_plan_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.PlaywrightAutomationRepository(root=root)

            result = repository.plan_playwright_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["automation"]["slug"], "login-smoke-check")
            self.assertEqual(result["browser"], "chromium")
            self.assertEqual(result["write_policy"], "read_only")
            self.assertFalse((root / "playwright_automation.py").exists())
            planned_paths = {item["path"] for item in result["planned_artifacts"]}
            self.assertIn("playwright_automation.py", planned_paths)

    def test_plan_reports_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = root / "playwright-spec.yaml"
            spec_path.write_text("automation_name: incomplete\n", encoding="utf-8")
            repository = self.repository_module.PlaywrightAutomationRepository(root=root)

            result = repository.plan_playwright_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "needs-input")
            self.assertGreaterEqual(
                set(result["missing_fields"]),
                {"purpose", "browser", "selectors", "steps", "assertions", "auth_strategy", "side_effects"},
            )

    def test_plan_blocks_secret_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, purpose="Login with PASSWORD=abc in the page.")
            repository = self.repository_module.PlaywrightAutomationRepository(root=root)

            result = repository.plan_playwright_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "forbidden_sensitive_marker")

    def test_generate_playwright_script_contains_required_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.PlaywrightAutomationRepository(root=root)

            result = repository.generate_playwright_script(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            content = result["content"]
            self.assertIn("sync_playwright", content)
            self.assertIn("--dry-run", content)
            self.assertIn("--execute", content)
            self.assertIn("--headless", content)
            self.assertIn("--browser", content)
            self.assertIn("--screenshot-dir", content)
            self.assertIn("--trace-dir", content)
            self.assertIn("context.tracing.start", content)
            py_compile.compile(str(self.write_temp_script(root, content)), doraise=True)

    def test_generated_script_dry_run_does_not_import_playwright(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.PlaywrightAutomationRepository(root=root)
            script_path = self.write_temp_script(root, repository.generate_playwright_script(spec_path=spec_path)["content"])

            result = subprocess.run(
                [sys.executable, str(script_path), "--dry-run"],
                cwd=root,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["plan"]["automation"], "login-smoke-check")

    def test_generate_project_files_dry_run_and_execute(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.PlaywrightAutomationRepository(root=root)

            planned = repository.generate_playwright_project_files(spec_path=spec_path)
            written = repository.generate_playwright_project_files(spec_path=spec_path, execute=True)

            self.assertEqual(planned["status"], "planned")
            self.assertTrue(planned["dry_run"])
            self.assertEqual(written["status"], "written")
            self.assertTrue((target_project / "login-smoke-check" / "playwright_automation.py").exists())

    def test_run_playwright_check_is_plan_first_and_blocks_unconfirmed_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            read_spec = self.write_spec(root)
            submit_spec = self.write_spec(root, automation_name="Submit Form", side_effects="form-submit")
            repository = self.repository_module.PlaywrightAutomationRepository(root=root)

            planned = repository.run_playwright_check(spec_path=read_spec)
            blocked = repository.run_playwright_check(spec_path=submit_spec, execute=True)

            self.assertEqual(planned["status"], "planned")
            self.assertTrue(planned["dry_run"])
            self.assertEqual(blocked["status"], "blocked")
            self.assertEqual(blocked["reason"], "confirmation_required")

    def test_review_playwright_artifacts_detects_missing_and_accepts_generated_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.PlaywrightAutomationRepository(root=root)
            script = repository.generate_playwright_script(spec_path=spec_path)["content"]

            script_review = repository.review_playwright_artifacts(paths=[], text=script)
            missing_review = repository.review_playwright_artifacts(paths=[root / "missing-trace.zip"])

            self.assertTrue(script_review["valid"], script_review["findings"])
            self.assertEqual(missing_review["status"], "failed")
            self.assertTrue(any("missing" in finding for finding in missing_review["findings"]))

    def test_wrap_playwright_as_capability_execute_writes_compilable_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.PlaywrightAutomationRepository(root=root)

            result = repository.wrap_playwright_as_capability(
                spec_path=spec_path,
                agent_id="web-ops-agent",
                capability_id="login-smoke-check",
                execute=True,
            )

            self.assertEqual(result["status"], "written")
            runner = target_project / "agents" / "web-ops-agent" / "capabilities" / "login-smoke-check" / "runner.py"
            self.assertTrue(runner.exists())
            py_compile.compile(str(runner), doraise=True)

    def test_plan_playwright_automation_runner_is_executable_through_agent_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = self.write_spec(Path(tmpdir))

            result = subprocess.run(
                [
                    sys.executable,
                    str(AGENT),
                    "--json",
                    "run",
                    "playwright-automation-builder",
                    "plan-playwright-automation",
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
        self.assertEqual(runner_payload["automation"]["slug"], "login-smoke-check")

    def write_temp_script(self, root: Path, content: str) -> Path:
        script = root / "playwright_automation.py"
        script.write_text(content, encoding="utf-8")
        return script


if __name__ == "__main__":
    unittest.main()
