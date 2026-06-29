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
REQUIRED_CORE_AGENTS = {
    "azure-devops-orchestrator",
    "aws-cloudwatch-log-analyzer",
    "database-change-operator",
    "elasticsearch-log-analyzer",
    "execution-reviewer",
    "github-pr-reviewer",
    "local-llm-operator",
    "n1-support-agent",
    "n2-support-agent",
    "postgres-data-analyzer",
    "provider-configurator",
    "sqlserver-data-analyzer",
    "task-orchestrator",
    "topdesk-orchestrator",
}
REQUIRED_MVP_PROVIDERS = {
    "aws",
    "azure-devops",
    "bpo",
    "elasticsearch",
    "figma",
    "postgres",
    "sqlserver",
    "technical-http",
    "topdesk",
}
REQUIRED_PLUGINS = {
    "codex-ai-devkit",
    "claude-code-ai-devkit",
    "claude-skill-ai-devkit",
}


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

    def write_minimal_agent_repo(self, root: Path, *, write_policy: str, agent_write_policy: str | None = None) -> None:
        agent = root / "agents" / "sample-agent"
        capability = agent / "capabilities" / "sample-capability"
        capability.mkdir(parents=True)
        (root / "README.md").write_text("- `sample-agent`: sample.\n", encoding="utf-8")
        (root / "providers").mkdir()
        agents_readme = root / "agents" / "README.md"
        agents_readme.write_text("- `sample-agent`: sample.\n", encoding="utf-8")
        (agent / "AGENTS.md").write_text("# Sample\n", encoding="utf-8")
        (agent / "README.md").write_text("# Sample\n", encoding="utf-8")
        (agent / "knowledge").mkdir()
        (agent / "templates").mkdir()
        (agent / "infra").mkdir()
        agent_policy = f"write_policy: {agent_write_policy}\n" if agent_write_policy else ""
        (agent / "agent.yaml").write_text(
            f"""
id: sample-agent
kind: specialist-agent
name: Sample Agent
version: 0.1.0
status: draft
owner: test
purpose: Sample agent.
default_context: []
capabilities:
  - sample-capability
{agent_policy}""".lstrip(),
            encoding="utf-8",
        )
        (capability / "workflow.md").write_text("# Workflow\n", encoding="utf-8")
        (capability / "decision-rules.md").write_text("# Rules\n", encoding="utf-8")
        (capability / "capability.yaml").write_text(
            f"""
id: sample-capability
kind: capability
name: Sample Capability
version: 0.1.0
status: draft
purpose: Sample capability.
entrypoint: {{}}
inputs: {{}}
outputs: {{}}
write_policy: {write_policy}
""".lstrip(),
            encoding="utf-8",
        )

    def test_current_repo_passes_default_validation(self) -> None:
        result = self.run_validator("--json")

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        summary = payload["summary"]
        self.assertGreaterEqual(summary["agents"], len(REQUIRED_CORE_AGENTS))
        self.assertGreaterEqual(summary["capabilities"], summary["agents"])
        self.assertGreater(summary["declared_runners"], 0)
        self.assertLessEqual(summary["declared_runners"], summary["capabilities"])
        self.assertEqual(payload["summary"]["missing_decision_rules"], 0)
        self.assertGreaterEqual(summary["providers"], len(REQUIRED_MVP_PROVIDERS))
        self.assertGreaterEqual(summary["plugins"], len(REQUIRED_PLUGINS))
        self.assertFalse(REQUIRED_CORE_AGENTS - set(payload["agents"]))
        self.assertFalse(REQUIRED_MVP_PROVIDERS - set(payload["providers"]))
        for agent_id, stats in payload["agents"].items():
            self.assertEqual(stats["missing_decision_rules"], 0, agent_id)
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

    def test_detects_unknown_capability_write_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.write_minimal_agent_repo(root, write_policy="write_whenever")

            result = self.run_validator("--json", root=root)

        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml has unsupported write_policy: 'write_whenever'",
            payload["errors"],
        )

    def test_warns_on_legacy_write_policy_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.write_minimal_agent_repo(root, write_policy="read-only", agent_write_policy="ask_before_write")

            result = self.run_validator("--json", root=root)
            strict_result = self.run_validator("--json", "--strict", root=root)

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertNotEqual(strict_result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn(
            "agents/sample-agent/agent.yaml uses legacy write_policy: 'ask_before_write'; use 'confirm'",
            payload["warnings"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml uses legacy write_policy: 'read-only'; use 'read_only'",
            payload["warnings"],
        )

    def test_validates_agent_mode_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.write_minimal_agent_repo(root, write_policy="read_only")
            agent_manifest = root / "agents" / "sample-agent" / "agent.yaml"
            agent_manifest.write_text(
                agent_manifest.read_text(encoding="utf-8")
                + """
agent_mode:
  type: improviser
  max_steps: 0
  max_specialists: 0
  max_llm_calls: -1
  can_call_capabilities: "yes"
  can_call_llm: always
  allowed_capabilities: not-a-list
  external_writes: true
""",
                encoding="utf-8",
            )

            result = self.run_validator("--json", root=root)

        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn("agents/sample-agent/agent.yaml agent_mode.type has unsupported value: improviser", payload["errors"])
        self.assertIn("agents/sample-agent/agent.yaml agent_mode.max_steps must be an integer between 1 and 20", payload["errors"])
        self.assertIn("agents/sample-agent/agent.yaml agent_mode.max_specialists must be an integer between 1 and 20", payload["errors"])
        self.assertIn("agents/sample-agent/agent.yaml agent_mode.max_llm_calls must be an integer between 0 and 20", payload["errors"])
        self.assertIn("agents/sample-agent/agent.yaml agent_mode.can_call_capabilities must be boolean", payload["errors"])
        self.assertIn("agents/sample-agent/agent.yaml agent_mode.can_call_llm must be false, optional, or required", payload["errors"])
        self.assertIn("agents/sample-agent/agent.yaml agent_mode.allowed_capabilities must be a list", payload["errors"])
        self.assertIn(
            "agents/sample-agent/agent.yaml agent_mode.external_writes=true requires confirm, delegated, or blocked_by_default write_policy",
            payload["errors"],
        )

    def test_detects_invalid_routing_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.write_minimal_agent_repo(root, write_policy="read_only")
            agent_manifest = root / "agents" / "sample-agent" / "agent.yaml"
            agent_manifest.write_text(
                agent_manifest.read_text(encoding="utf-8")
                + """
routing:
  anchors: not-a-list
  domains: not-a-list
  keywords:
    - ""
  intents:
    - ""
  priority: high
""",
                encoding="utf-8",
            )
            capability_manifest = root / "agents" / "sample-agent" / "capabilities" / "sample-capability" / "capability.yaml"
            capability_manifest.write_text(
                capability_manifest.read_text(encoding="utf-8")
                + """
routing:
  aliases: not-a-list
  entities:
    - ""
  examples: not-a-list
""",
                encoding="utf-8",
            )

            result = self.run_validator("--json", root=root)

        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn("agents/sample-agent/agent.yaml routing.anchors must be a list", payload["errors"])
        self.assertIn("agents/sample-agent/agent.yaml routing.domains must be a list", payload["errors"])
        self.assertIn("agents/sample-agent/agent.yaml routing.keywords entries must be non-empty strings", payload["errors"])
        self.assertIn("agents/sample-agent/agent.yaml routing.intents entries must be non-empty strings", payload["errors"])
        self.assertIn("agents/sample-agent/agent.yaml routing.priority must be an integer", payload["errors"])
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml routing.aliases must be a list",
            payload["errors"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml routing.entities entries must be non-empty strings",
            payload["errors"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml routing.examples must be a list",
            payload["errors"],
        )

    def test_detects_invalid_runtime_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.write_minimal_agent_repo(root, write_policy="read_only")
            capability_manifest = root / "agents" / "sample-agent" / "capabilities" / "sample-capability" / "capability.yaml"
            capability_manifest.write_text(
                capability_manifest.read_text(encoding="utf-8")
                + """
runtime:
  provider: missing-provider
  source:
    enabled: "yes"
    args:
      project: project
    env:
      project: not-valid-env-name!
""",
                encoding="utf-8",
            )

            result = self.run_validator("--json", root=root)

        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml runtime references unknown provider: missing-provider",
            payload["errors"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml runtime.source.enabled must be boolean",
            payload["errors"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml runtime.source.args.project must map to a CLI flag",
            payload["errors"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml runtime.source.env.project must map to an environment variable",
            payload["errors"],
        )

    def test_detects_invalid_runtime_role_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.write_minimal_agent_repo(root, write_policy="read_only")
            agent_manifest = root / "agents" / "sample-agent" / "agent.yaml"
            agent_manifest.write_text(
                agent_manifest.read_text(encoding="utf-8").replace(
                    "kind: specialist-agent",
                    "kind: runtime-agent",
                ),
                encoding="utf-8",
            )

            result = self.run_validator("--json", root=root)

        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn("agents/sample-agent/agent.yaml runtime-agent must declare runtime_role", payload["errors"])

    def test_detects_invalid_top_level_source_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.write_minimal_agent_repo(root, write_policy="read_only")
            capability_manifest = root / "agents" / "sample-agent" / "capabilities" / "sample-capability" / "capability.yaml"
            capability_manifest.write_text(
                capability_manifest.read_text(encoding="utf-8")
                + """
source:
  supported: "yes"
  mappings:
    - field: project
      arg: project
      env: not-valid-env-name!
""",
                encoding="utf-8",
            )

            result = self.run_validator("--json", root=root)

        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml source.supported must be boolean",
            payload["errors"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml source.mappings[0].arg must map to a CLI flag",
            payload["errors"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml source.mappings[0].env must map to an environment variable",
            payload["errors"],
        )

    def test_detects_invalid_capability_execution_and_artifacts_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.write_minimal_agent_repo(root, write_policy="read_only")
            capability_manifest = root / "agents" / "sample-agent" / "capabilities" / "sample-capability" / "capability.yaml"
            capability_manifest.write_text(
                capability_manifest.read_text(encoding="utf-8")
                + """
execution:
  modes:
    - execute-now
  idempotency: random
  timeout_seconds: 0
  unknown: true
outputs:
  artifacts:
    - path: report.bin
      kind: binary
      sensitive: "no"
""",
                encoding="utf-8",
            )

            result = self.run_validator("--json", root=root)

        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml execution has unsupported field: unknown",
            payload["errors"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml execution.modes has unsupported mode: execute-now",
            payload["errors"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml execution.idempotency has unsupported value: random",
            payload["errors"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml execution.timeout_seconds must be a positive integer",
            payload["errors"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml outputs.artifacts has unsupported kind: binary",
            payload["errors"],
        )
        self.assertIn(
            "agents/sample-agent/capabilities/sample-capability/capability.yaml outputs.artifacts sensitive must be boolean",
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
        self.assertGreaterEqual(payload["summary"]["plugins"], len(REQUIRED_PLUGINS))
        self.assertFalse(REQUIRED_PLUGINS - set(payload["plugins"]))


if __name__ == "__main__":
    unittest.main()
