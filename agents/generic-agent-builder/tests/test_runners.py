#!/usr/bin/env python3
"""Tests for the Generic Agent Builder runners."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "agent"
AGENT_DIR = ROOT / "agents" / "generic-agent-builder"
REPOSITORY_PATH = AGENT_DIR / "infra" / "integrations" / "generic-agent" / "generic_agent_repository.py"


def load_repository_module():
    spec = importlib.util.spec_from_file_location("generic_agent_repository", REPOSITORY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load repository from {REPOSITORY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GenericAgentBuilderRunnersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_module = load_repository_module()

    def write_spec(
        self,
        root: Path,
        *,
        target_host: str = "generic",
        target_project: Path | None = None,
        domain_context: str = "Support triage for internal software projects.",
    ) -> Path:
        path = root / "generic-agent-spec.yaml"
        target_project_line = f"target_project: {target_project}\n" if target_project else ""
        path.write_text(
            f"""
target_host: {target_host}
{target_project_line}agent_name: Support Review Agent
purpose: >
  Review support tickets and produce concise operational guidance.
allowed_tools:
  - shell
  - file_search
forbidden_actions:
  - write secrets
  - bypass host permissions
domain_context: {domain_context}
output_format: Markdown report with facts, risks and next steps.
quality_gates:
  - cite assumptions
  - ask human before external writes
""".lstrip(),
            encoding="utf-8",
        )
        return path

    def test_plan_generic_agent_returns_host_profile_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.GenericAgentRepository(root=root)

            result = repository.plan_generic_agent(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["target_host"], "generic")
            planned_paths = {item["path"] for item in result["planned_artifacts"]}
            self.assertIn("AGENTS.md", planned_paths)
            self.assertFalse((root / "AGENTS.md").exists())

    def test_plan_generic_agent_reports_needs_input_for_incomplete_spec(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = root / "generic-agent-spec.yaml"
            spec_path.write_text("target_host: generic\n", encoding="utf-8")
            repository = self.repository_module.GenericAgentRepository(root=root)

            result = repository.plan_generic_agent(spec_path=spec_path)

            self.assertEqual(result["status"], "needs-input")
            self.assertGreaterEqual(set(result["missing_fields"]), {"agent_name", "purpose", "domain_context"})

    def test_generate_agent_instructions_contains_guardrails_and_limits(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.GenericAgentRepository(root=root)

            result = repository.generate_agent_instructions(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            content = result["content"]
            self.assertIn("## Role", content)
            self.assertIn("## Workflow", content)
            self.assertIn("## Guardrails", content)
            self.assertIn("## Human Escalation", content)
            self.assertIn("Ask a human", content)
            self.assertIn("bypass host permissions", content)

    def test_generate_skill_returns_skill_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, target_host="claude")
            repository = self.repository_module.GenericAgentRepository(root=root)

            result = repository.generate_skill(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            self.assertIn("---", result["content"])
            self.assertIn("name: support-review-agent", result["content"])
            self.assertIn("# Support Review Agent", result["content"])
            self.assertFalse((root / "SKILL.md").exists())

    def test_generate_project_agent_files_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.GenericAgentRepository(root=root)

            result = repository.generate_project_agent_files(spec_path=spec_path)

            self.assertEqual(result["status"], "planned")
            self.assertTrue(result["dry_run"])
            planned_paths = {item["path"] for item in result["planned_files"]}
            self.assertIn("AGENTS.md", planned_paths)
            self.assertFalse((target_project / "AGENTS.md").exists())

    def test_generate_project_agent_files_execute_writes_inside_target_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.GenericAgentRepository(root=root)

            result = repository.generate_project_agent_files(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "written")
            self.assertTrue((target_project / "AGENTS.md").exists())
            for item in result["written_files"]:
                path = Path(item["path"]).resolve()
                self.assertTrue(path.is_relative_to(target_project.resolve()), item["path"])

    def test_generate_project_agent_files_blocks_overwrite_without_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.GenericAgentRepository(root=root)
            repository.generate_project_agent_files(spec_path=spec_path, execute=True)

            result = repository.generate_project_agent_files(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "target_exists")

    def test_plan_generic_agent_blocks_secret_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, domain_context="Use API_KEY=abc during triage.")
            repository = self.repository_module.GenericAgentRepository(root=root)

            result = repository.plan_generic_agent(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "forbidden_sensitive_marker")

    def test_review_generic_agent_detects_missing_guardrails(self) -> None:
        repository = self.repository_module.GenericAgentRepository(root=ROOT)

        result = repository.review_generic_agent(text="# Agent\n\nAlways answer quickly.", target_host="generic")

        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "failed")
        self.assertTrue(any("guardrail" in finding.lower() for finding in result["findings"]))

    def test_plan_generic_agent_runner_is_executable_through_agent_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = self.write_spec(Path(tmpdir))

            result = subprocess.run(
                [
                    sys.executable,
                    str(AGENT),
                    "--json",
                    "run",
                    "generic-agent-builder",
                    "plan-generic-agent",
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
        self.assertEqual(runner_payload["target_host"], "generic")


if __name__ == "__main__":
    unittest.main()
