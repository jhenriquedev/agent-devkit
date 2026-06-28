#!/usr/bin/env python3
"""Tests for the global repository validation script."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-repo.py"


class ValidateRepoTest(unittest.TestCase):
    def run_validator(self, *args: str, root: Path = ROOT) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--root", str(root), *args],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

    def test_current_repo_passes_default_validation(self) -> None:
        result = self.run_validator("--json")

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["agents"], 23)
        self.assertEqual(payload["summary"]["capabilities"], 312)
        self.assertEqual(payload["summary"]["declared_runners"], 290)
        self.assertEqual(payload["summary"]["missing_decision_rules"], 0)
        self.assertEqual(payload["summary"]["providers"], 21)
        self.assertEqual(payload["summary"]["plugins"], 3)
        self.assertEqual(payload["agents"]["aws-architecture-analyst"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["aws-cloudwatch-log-analyzer"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["aws-operations-operator"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["aws-security-governance-auditor"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["azure-devops-orchestrator"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["bpo-analyser"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["data-scientist-analyst"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["database-change-operator"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["drawio-diagram-builder"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["elasticsearch-log-analyzer"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["excel-workbook-builder"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["figma-ui-ux-product-designer"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["github-pr-reviewer"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["knowledge-generator"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["n1-support-agent"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["n2-support-agent"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["postgres-data-analyzer"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["presentation-deck-builder"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["software-specification-analyst"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["sqlserver-change-operator"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["sqlserver-data-analyzer"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["technical-integration-analyst"]["missing_decision_rules"], 0)
        self.assertEqual(payload["agents"]["topdesk-orchestrator"]["missing_decision_rules"], 0)
        self.assertEqual(payload["errors"], [])

    def test_detects_missing_runner_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            agent = root / "agents" / "sample-agent"
            capability = agent / "capabilities" / "broken-capability"
            capability.mkdir(parents=True)
            (root / "README.md").write_text("- `sample-agent`: sample.\n", encoding="utf-8")
            agents_readme = root / "agents" / "README.md"
            agents_readme.write_text("- `sample-agent`: sample.\n", encoding="utf-8")
            (agent / "AGENTS.md").write_text("# Sample\n", encoding="utf-8")
            (agent / "README.md").write_text("# Sample\n", encoding="utf-8")
            (agent / "knowledge").mkdir()
            (agent / "templates").mkdir()
            (agent / "infra").mkdir()
            (agent / "agent.yaml").write_text(
                """
id: sample-agent
kind: specialist-agent
name: Sample Agent
version: 0.1.0
status: draft
owner: test
purpose: Sample agent.
default_context: []
capabilities:
  - broken-capability
""".lstrip(),
                encoding="utf-8",
            )
            (capability / "workflow.md").write_text("# Workflow\n", encoding="utf-8")
            (capability / "capability.yaml").write_text(
                """
id: broken-capability
kind: capability
name: Broken Capability
version: 0.1.0
status: draft
purpose: Broken capability.
entrypoint:
  runner: missing-runner.py
inputs: {}
outputs: {}
write_policy: read_only
""".lstrip(),
                encoding="utf-8",
            )

            result = self.run_validator("--json", root=root)

        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn(
            "agents/sample-agent/capabilities/broken-capability/capability.yaml declares missing runner missing-runner.py",
            payload["errors"],
        )

    def test_strict_mode_fails_on_root_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Empty\n", encoding="utf-8")
            (root / "agents").mkdir()
            (root / "agents" / "README.md").write_text("# Agents\n", encoding="utf-8")
            (root / "json").write_text("generated output\n", encoding="utf-8")

            result = self.run_validator("--json", "--strict", root=root)

        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn("root contains generated-looking artifact: json", payload["warnings"])

    def test_detects_provider_secret_field_without_secret_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Empty\n", encoding="utf-8")
            (root / "agents").mkdir()
            (root / "agents" / "README.md").write_text("# Agents\n", encoding="utf-8")
            providers = root / "providers"
            providers.mkdir()
            (providers / "sample-provider.yaml").write_text(
                """
id: sample-provider
name: Sample Provider
kind: remote-api
status: active
description: Sample provider.
auth_methods: []
config_fields:
  - name: SAMPLE_API_KEY
    required: true
    secret: false
capabilities:
  read: []
health_check:
  command: agent provider doctor sample-provider
risk:
  default: read
  writes: false
fallbacks:
  - manual_steps
""".lstrip(),
                encoding="utf-8",
            )

            result = self.run_validator("--json", root=root)

        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn(
            "providers/sample-provider.yaml config field SAMPLE_API_KEY looks secret but is not marked secret: true",
            payload["errors"],
        )

    def test_detects_invalid_capability_provider_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            agent = root / "agents" / "sample-agent"
            capability = agent / "capabilities" / "broken-capability"
            capability.mkdir(parents=True)
            (root / "README.md").write_text("- `sample-agent`: sample.\n", encoding="utf-8")
            agents_readme = root / "agents" / "README.md"
            agents_readme.write_text("- `sample-agent`: sample.\n", encoding="utf-8")
            providers = root / "providers"
            providers.mkdir()
            (providers / "known-provider.yaml").write_text(
                """
id: known-provider
name: Known Provider
kind: remote-api
status: active
description: Known provider.
auth_methods: []
config_fields: []
capabilities:
  read: []
health_check:
  command: agent provider doctor known-provider
risk:
  default: read
  writes: false
fallbacks:
  - manual_steps
""".lstrip(),
                encoding="utf-8",
            )
            (agent / "AGENTS.md").write_text("# Sample\n", encoding="utf-8")
            (agent / "README.md").write_text("# Sample\n", encoding="utf-8")
            (agent / "knowledge").mkdir()
            (agent / "templates").mkdir()
            (agent / "infra").mkdir()
            (agent / "agent.yaml").write_text(
                """
id: sample-agent
kind: specialist-agent
name: Sample Agent
version: 0.1.0
status: draft
owner: test
purpose: Sample agent.
default_context: []
capabilities:
  - broken-capability
""".lstrip(),
                encoding="utf-8",
            )
            (capability / "workflow.md").write_text("# Workflow\n", encoding="utf-8")
            (capability / "decision-rules.md").write_text("# Rules\n", encoding="utf-8")
            (capability / "runner.py").write_text("print('ok')\n", encoding="utf-8")
            (capability / "capability.yaml").write_text(
                """
id: broken-capability
kind: capability
name: Broken Capability
version: 0.1.0
status: draft
purpose: Broken capability.
entrypoint:
  runner: runner.py
inputs: {}
outputs: {}
write_policy: read_only
requires:
  providers:
    - id: missing-provider
      mode: wrong-mode
      fallback: wrong-fallback
""".lstrip(),
                encoding="utf-8",
            )

            result = self.run_validator("--json", root=root)

        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn(
            "agents/sample-agent/capabilities/broken-capability/capability.yaml requires unknown provider: missing-provider",
            payload["errors"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/broken-capability/capability.yaml provider missing-provider has unsupported mode: wrong-mode",
            payload["errors"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/broken-capability/capability.yaml provider missing-provider has unsupported fallback: wrong-fallback",
            payload["errors"],
        )

    def test_detects_invalid_plugin_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Empty\n", encoding="utf-8")
            (root / "agents").mkdir()
            (root / "agents" / "README.md").write_text("# Agents\n", encoding="utf-8")
            plugins = root / "plugins" / "broken-plugin"
            plugins.mkdir(parents=True)
            (plugins / "plugin.json").write_text('{"name": "Broken"}\n', encoding="utf-8")

            result = self.run_validator("--json", root=root)

        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn("plugins/broken-plugin/plugin.json missing required key: id", payload["errors"])
        self.assertIn("plugins/broken-plugin/plugin.json missing required key: version", payload["errors"])

    def test_codex_and_claude_plugins_have_expected_entrypoints(self) -> None:
        result = self.run_validator("--json")

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["plugins"], 3)
        self.assertIn("codex-ai-devkit", payload["plugins"])
        self.assertIn("claude-code-ai-devkit", payload["plugins"])
        self.assertIn("claude-skill-ai-devkit", payload["plugins"])


if __name__ == "__main__":
    unittest.main()
