#!/usr/bin/env python3
"""Tests for the Execution Loop Builder runners."""

from __future__ import annotations

import importlib.util
import json
import os
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "agent"
AGENT_DIR = ROOT / "agents" / "execution-loop-builder"
REPOSITORY_PATH = (
    AGENT_DIR
    / "infra"
    / "integrations"
    / "execution-loop"
    / "execution_loop_repository.py"
)


def load_repository_module():
    spec = importlib.util.spec_from_file_location("execution_loop_repository", REPOSITORY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load repository from {REPOSITORY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExecutionLoopBuilderRunnersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_module = load_repository_module()

    def write_spec(
        self,
        root: Path,
        *,
        target_project: Path | None = None,
        external_writes: bool = False,
        dry_run_supported: bool = True,
        idempotency_key: str = "",
        command: str | None = None,
        missing_budget: bool = False,
    ) -> Path:
        path = root / "loop-spec.yaml"
        target_project_line = f"target_project: {target_project}\n" if target_project else ""
        budget_block = "" if missing_budget else """
budget:
  max_iterations: 3
  max_runtime_seconds: 120
  max_llm_calls: 1
"""
        idempotency_line = f"  idempotency_key: {idempotency_key}\n" if idempotency_key else ""
        step_block = (
            f"  - id: cleanup\n    type: command\n    command: {json.dumps(command)}\n"
            if command
            else "  - id: list-prs\n    capability: github-pr-reviewer.list-review-requests\n"
        )
        path.write_text(
            f"""
id: daily-pr-review
objective: Review pending PRs and produce a report.
{target_project_line}trigger:
  type: schedule
  every: 30m
{budget_block}side_effects:
  external_writes: {str(external_writes).lower()}
  dry_run_supported: {str(dry_run_supported).lower()}
{idempotency_line}steps:
{step_block}success_when:
  - report_generated
stop_when:
  - no_items
  - max_iterations_reached
notify:
  on: [failure, completion]
  channels: [terminal]
  max_per_run: 2
""".lstrip(),
            encoding="utf-8",
        )
        return path

    def test_plan_execution_loop_returns_contract_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.ExecutionLoopRepository(root=ROOT)

            result = repository.plan_execution_loop(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["write_policy"], "read_only")
            self.assertEqual(result["loop"]["id"], "daily-pr-review")
            self.assertEqual(result["loop"]["max_iterations"], 3)
            planned = {item["path"] for item in result["planned_artifacts"]}
            self.assertIn("daily-pr-review/loop_runner.py", planned)
            self.assertFalse((root / "daily-pr-review").exists())

    def test_plan_reports_missing_required_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, missing_budget=True)
            repository = self.repository_module.ExecutionLoopRepository(root=ROOT)

            result = repository.plan_execution_loop(spec_path=spec_path)

            self.assertEqual(result["status"], "needs-input")
            self.assertIn("budget", result["missing_fields"])

    def test_plan_blocks_external_writes_without_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, external_writes=True, dry_run_supported=False)
            repository = self.repository_module.ExecutionLoopRepository(root=ROOT)

            result = repository.plan_execution_loop(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            codes = {finding["code"] for finding in result["findings"]}
            self.assertIn("external_write_without_dry_run", codes)

    def test_generate_loop_runner_returns_content_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.ExecutionLoopRepository(root=ROOT)

            result = repository.generate_loop_runner(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["write_policy"], "output_only")
            self.assertIn("LOOP_SPEC", result["content"])
            self.assertIn("max_iterations", result["content"])
            self.assertFalse((root / "loop_runner.py").exists())

    def test_generate_loop_project_files_dry_run_and_execute(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.ExecutionLoopRepository(root=ROOT)

            planned = repository.generate_loop_project_files(spec_path=spec_path)
            written = repository.generate_loop_project_files(spec_path=spec_path, execute=True)

            self.assertEqual(planned["status"], "planned")
            self.assertTrue(planned["dry_run"])
            self.assertEqual(written["status"], "written")
            runner = target_project / "daily-pr-review" / "loop_runner.py"
            self.assertTrue(runner.exists())
            py_compile.compile(str(runner), doraise=True)
            for item in written["written_files"]:
                self.assertTrue(Path(item["path"]).resolve().is_relative_to(target_project.resolve()))

    def test_generate_loop_project_files_blocks_overwrite_without_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.ExecutionLoopRepository(root=ROOT)
            repository.generate_loop_project_files(spec_path=spec_path, execute=True)

            result = repository.generate_loop_project_files(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "target_exists")

    def test_review_loop_safety_detects_text_risks(self) -> None:
        repository = self.repository_module.ExecutionLoopRepository(root=ROOT)

        result = repository.review_loop_safety(text="while true: rm -rf /tmp/x API_KEY=abc")

        self.assertEqual(result["status"], "failed")
        codes = {finding["code"] for finding in result["findings"]}
        self.assertIn("missing_max_iterations", codes)
        self.assertIn("missing_max_runtime_seconds", codes)
        self.assertIn("missing_stop_when", codes)
        self.assertIn("destructive_step", codes)
        rendered = json.dumps(result)
        self.assertNotIn("abc", rendered)

    def test_review_loop_safety_detects_external_write_without_idempotency(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, external_writes=True)
            repository = self.repository_module.ExecutionLoopRepository(root=ROOT)

            result = repository.review_loop_safety(spec_path=spec_path)

            self.assertEqual(result["status"], "failed")
            codes = {finding["code"] for finding in result["findings"]}
            self.assertIn("external_write_without_idempotency", codes)

    def test_register_loop_task_dry_run_does_not_write_scheduler(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            os.environ["AI_DEVKIT_CONFIG_HOME"] = str(root / "home")
            repository = self.repository_module.ExecutionLoopRepository(root=ROOT)
            try:
                result = repository.register_loop_task(spec_path=spec_path)
            finally:
                os.environ.pop("AI_DEVKIT_CONFIG_HOME", None)

            self.assertEqual(result["status"], "planned")
            self.assertTrue(result["dry_run"])
            self.assertFalse((root / "home" / "tasks" / "tasks.json").exists())

    def test_register_loop_task_execute_uses_local_scheduler(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            home = root / "home"
            spec_path = self.write_spec(root)
            old_home = os.environ.get("AI_DEVKIT_CONFIG_HOME")
            os.environ["AI_DEVKIT_CONFIG_HOME"] = str(home)
            repository = self.repository_module.ExecutionLoopRepository(root=ROOT)
            try:
                result = repository.register_loop_task(spec_path=spec_path, execute=True)
            finally:
                if old_home is None:
                    os.environ.pop("AI_DEVKIT_CONFIG_HOME", None)
                else:
                    os.environ["AI_DEVKIT_CONFIG_HOME"] = old_home

            self.assertEqual(result["status"], "registered")
            self.assertEqual(result["task"]["id"], "daily-pr-review")
            self.assertEqual(result["task"]["schedule"]["type"], "interval")
            self.assertEqual(result["task"]["action"]["type"], "loop-runner")
            self.assertFalse(result["task"]["action"]["external_writes"])

    def test_plan_runner_is_executable_through_agent_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)

            result = subprocess.run(
                [
                    sys.executable,
                    str(AGENT),
                    "--json",
                    "run",
                    "execution-loop-builder",
                    "plan-execution-loop",
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
        self.assertEqual(runner_payload["loop"]["id"], "daily-pr-review")


if __name__ == "__main__":
    unittest.main()
