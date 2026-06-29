#!/usr/bin/env python3
"""Tests for the Agent DevKit Agent Builder runners."""

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
AGENT_DIR = ROOT / "agents" / "agent-devkit-agent-builder"
REPOSITORY_PATH = AGENT_DIR / "infra" / "integrations" / "agent-devkit" / "agent_builder_repository.py"


def load_repository_module():
    spec = importlib.util.spec_from_file_location("agent_builder_repository", REPOSITORY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load repository from {REPOSITORY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AgentBuilderRunnersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_module = load_repository_module()

    def write_spec(self, root: Path, *, agent_id: str = "sample-builder-agent") -> Path:
        path = root / "agent-spec.yaml"
        path.write_text(
            f"""
agent_id: {agent_id}
name: Sample Builder Agent
purpose: >
  Criar artefatos de exemplo para validar o builder interno do Agent DevKit.
domain: internal tooling
capabilities:
  - id: inspect-sample
    purpose: Inspecionar uma fonte local em modo read-only.
    write_policy: read_only
providers: []
risk_profile: low
""".lstrip(),
            encoding="utf-8",
        )
        return path

    def test_plan_agent_returns_planned_files_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.AgentBuilderRepository(root=root)

            result = repository.plan_agent(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["agent"]["id"], "sample-builder-agent")
            planned_paths = {item["path"] for item in result["planned_files"]}
            self.assertGreaterEqual(
                planned_paths,
                {
                    "agents/sample-builder-agent/agent.yaml",
                    "agents/sample-builder-agent/AGENTS.md",
                    "agents/sample-builder-agent/README.md",
                    "agents/sample-builder-agent/capabilities/inspect-sample/capability.yaml",
                    "agents/sample-builder-agent/capabilities/inspect-sample/workflow.md",
                    "agents/sample-builder-agent/capabilities/inspect-sample/decision-rules.md",
                },
            )
            self.assertFalse((root / "agents" / "sample-builder-agent").exists())

    def test_plan_agent_reports_needs_input_for_incomplete_spec(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = root / "agent-spec.yaml"
            spec_path.write_text("agent_id: incomplete-agent\n", encoding="utf-8")
            repository = self.repository_module.AgentBuilderRepository(root=root)

            result = repository.plan_agent(spec_path=spec_path)

            self.assertEqual(result["status"], "needs-input")
            self.assertGreaterEqual(set(result["missing_fields"]), {"name", "purpose", "domain", "capabilities"})

    def test_scaffold_agent_dry_run_does_not_write_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.AgentBuilderRepository(root=root)

            result = repository.scaffold_agent(spec_path=spec_path, execute=False)

            self.assertEqual(result["status"], "planned")
            self.assertTrue(result["dry_run"])
            self.assertFalse((root / "agents" / "sample-builder-agent").exists())

    def test_scaffold_agent_execute_writes_only_inside_agent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.AgentBuilderRepository(root=root)

            result = repository.scaffold_agent(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "written")
            agent_root = root / "agents" / "sample-builder-agent"
            self.assertTrue((agent_root / "agent.yaml").exists())
            self.assertTrue((agent_root / "AGENTS.md").exists())
            self.assertTrue((agent_root / "README.md").exists())
            self.assertTrue((agent_root / "knowledge" / "system.md").exists())
            self.assertTrue((agent_root / "templates" / "README.md").exists())
            self.assertTrue((agent_root / "infra" / "README.md").exists())
            for item in result["written_files"]:
                path = (root / item["path"]).resolve()
                self.assertTrue(path.is_relative_to(agent_root.resolve()), item["path"])

    def test_scaffold_agent_blocks_overwrite_without_explicit_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.AgentBuilderRepository(root=root)
            repository.scaffold_agent(spec_path=spec_path, execute=True)

            result = repository.scaffold_agent(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "agent_exists")

    def test_plan_agent_blocks_path_traversal_agent_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, agent_id="../bad-agent")
            repository = self.repository_module.AgentBuilderRepository(root=root)

            result = repository.plan_agent(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "invalid_agent_id")

    def test_validate_agent_contract_accepts_generated_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.AgentBuilderRepository(root=root)
            repository.scaffold_agent(spec_path=spec_path, execute=True)

            result = repository.validate_agent_contract(agent_id="sample-builder-agent")

            self.assertTrue(result["valid"])
            self.assertEqual(result["errors"], [])

    def test_plan_agent_runner_is_executable_through_agent_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = self.write_spec(Path(tmpdir))

            result = subprocess.run(
                [
                    sys.executable,
                    str(AGENT),
                    "--json",
                    "run",
                    "agent-devkit-agent-builder",
                    "plan-agent",
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
        self.assertEqual(runner_payload["agent"]["id"], "sample-builder-agent")


if __name__ == "__main__":
    unittest.main()
