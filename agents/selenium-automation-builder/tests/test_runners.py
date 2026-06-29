#!/usr/bin/env python3
"""Tests for the Selenium Automation Builder runners."""

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
AGENT_DIR = ROOT / "agents" / "selenium-automation-builder"
REPOSITORY_PATH = AGENT_DIR / "infra" / "integrations" / "selenium-automation" / "selenium_automation_repository.py"


def load_repository_module():
    spec = importlib.util.spec_from_file_location("selenium_automation_repository", REPOSITORY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load repository from {REPOSITORY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SeleniumAutomationBuilderRunnersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_module = load_repository_module()

    def write_spec(
        self,
        root: Path,
        *,
        automation_name: str = "Legacy Login Check",
        target_project: Path | None = None,
        selenium_reasons: list[str] | None = None,
        purpose: str = "Check a legacy login page through WebDriver-compatible browser automation.",
        side_effects: str = "read-only",
    ) -> Path:
        path = root / "selenium-spec.yaml"
        target_project_line = f"target_project: {target_project}\n" if target_project else ""
        reasons = ["webdriver-required"] if selenium_reasons is None else selenium_reasons
        reason_block = "selenium_reasons: []" if not reasons else "selenium_reasons:\n" + "\n".join(f"  - {item}" for item in reasons)
        path.write_text(
            f"""
automation_name: {automation_name}
{target_project_line}purpose: {purpose}
target_url: https://example.test/login
browser: chrome
remote_url_env: SELENIUM_REMOTE_URL
auth_strategy: env
side_effects: {side_effects}
{reason_block}
selectors:
  - name: username
    by: css
    value: '[name="username"]'
  - name: submit
    by: css
    value: 'button[type="submit"]'
steps:
  - open target_url
  - wait for username
  - capture status
quality_gates:
  - explicit waits are used
  - screenshot is captured on failure
""".lstrip(),
            encoding="utf-8",
        )
        return path

    def test_plan_selenium_automation_returns_plan_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.SeleniumAutomationRepository(root=root)

            result = repository.plan_selenium_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["automation"]["slug"], "legacy-login-check")
            self.assertEqual(result["browser"], "chrome")
            self.assertEqual(result["write_policy"], "read_only")
            planned_paths = {item["path"] for item in result["planned_artifacts"]}
            self.assertIn("selenium_automation.py", planned_paths)
            self.assertFalse((root / "selenium_automation.py").exists())

    def test_plan_selenium_automation_reports_needs_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = root / "selenium-spec.yaml"
            spec_path.write_text("automation_name: incomplete\n", encoding="utf-8")
            repository = self.repository_module.SeleniumAutomationRepository(root=root)

            result = repository.plan_selenium_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "needs-input")
            self.assertGreaterEqual(
                set(result["missing_fields"]),
                {"purpose", "browser", "selectors", "steps", "auth_strategy", "side_effects", "selenium_reasons"},
            )

    def test_plan_recommends_playwright_when_selenium_not_justified(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, selenium_reasons=[])
            repository = self.repository_module.SeleniumAutomationRepository(root=root)

            result = repository.plan_selenium_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "needs-playwright-review")
            self.assertEqual(result["reason"], "selenium_not_justified")
            self.assertIn("problem 27", " ".join(result["next_steps"]).lower())

    def test_plan_blocks_secret_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, purpose="Login with PASSWORD=abc in the page.")
            repository = self.repository_module.SeleniumAutomationRepository(root=root)

            result = repository.plan_selenium_automation(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "forbidden_sensitive_marker")

    def test_generate_selenium_script_contains_required_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.SeleniumAutomationRepository(root=root)

            result = repository.generate_selenium_script(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            content = result["content"]
            self.assertIn("WebDriverWait", content)
            self.assertIn("--headless", content)
            self.assertIn("--browser", content)
            self.assertIn("--remote-url", content)
            self.assertIn("--dry-run", content)
            self.assertIn("--confirm", content)
            self.assertIn("save_screenshot", content)
            self.assertNotIn("time.sleep", content)
            py_compile.compile(str(self.write_temp_script(root, content)), doraise=True)

    def test_generate_selenium_project_files_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.SeleniumAutomationRepository(root=root)

            result = repository.generate_selenium_project_files(spec_path=spec_path)

            self.assertEqual(result["status"], "planned")
            self.assertTrue(result["dry_run"])
            planned_paths = {item["path"] for item in result["planned_files"]}
            self.assertGreaterEqual(
                planned_paths,
                {
                    "legacy-login-check/selenium_automation.py",
                    "legacy-login-check/README.md",
                    "legacy-login-check/tests/test_selenium_automation.py",
                },
            )
            self.assertFalse((target_project / "legacy-login-check").exists())

    def test_generate_selenium_project_files_execute_writes_inside_target_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.SeleniumAutomationRepository(root=root)

            result = repository.generate_selenium_project_files(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "written")
            self.assertTrue((target_project / "legacy-login-check" / "selenium_automation.py").exists())
            for item in result["written_files"]:
                path = Path(item["path"]).resolve()
                self.assertTrue(path.is_relative_to(target_project.resolve()), item["path"])

    def test_generate_selenium_project_files_blocks_overwrite_without_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.SeleniumAutomationRepository(root=root)
            repository.generate_selenium_project_files(spec_path=spec_path, execute=True)

            result = repository.generate_selenium_project_files(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "target_exists")

    def test_review_selenium_script_detects_missing_explicit_waits(self) -> None:
        repository = self.repository_module.SeleniumAutomationRepository(root=ROOT)

        result = repository.review_selenium_script(text="driver.find_element('css selector', '#x')", side_effects="read-only")

        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "failed")
        self.assertTrue(any("webdriverwait" in finding.lower() for finding in result["findings"]))

    def test_review_selenium_script_accepts_generated_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.SeleniumAutomationRepository(root=root)
            script = repository.generate_selenium_script(spec_path=spec_path)["content"]

            result = repository.review_selenium_script(text=script, side_effects="read-only")

            self.assertTrue(result["valid"], result["findings"])
            self.assertEqual(result["findings"], [])

    def test_wrap_selenium_as_capability_execute_writes_compilable_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.SeleniumAutomationRepository(root=root)

            result = repository.wrap_selenium_as_capability(
                spec_path=spec_path,
                agent_id="web-ops-agent",
                capability_id="legacy-login-check",
                execute=True,
            )

            self.assertEqual(result["status"], "written")
            runner = target_project / "agents" / "web-ops-agent" / "capabilities" / "legacy-login-check" / "runner.py"
            self.assertTrue(runner.exists())
            py_compile.compile(str(runner), doraise=True)

    def test_plan_selenium_automation_runner_is_executable_through_agent_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = self.write_spec(Path(tmpdir))

            result = subprocess.run(
                [
                    sys.executable,
                    str(AGENT),
                    "--json",
                    "run",
                    "selenium-automation-builder",
                    "plan-selenium-automation",
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
        self.assertEqual(runner_payload["automation"]["slug"], "legacy-login-check")

    def write_temp_script(self, root: Path, content: str) -> Path:
        script = root / "selenium_automation.py"
        script.write_text(content, encoding="utf-8")
        return script


if __name__ == "__main__":
    unittest.main()
