"""Tests for figma-ui-ux-product-designer.

Covers:
  - detect_mode: all 4 modes
  - validate_execution_payload: gate de evidencia real
  - render_azure_context: modo degradado e flag de delegacao
  - render_documents: geracao de artefatos por operacao
  - knowledge/system.md: nao vazio
  - workflow.md: nenhum placeholder (todos tem OBJETIVO)
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
INFRA_DIR = AGENT_DIR / "infra" / "integrations" / "figma"
SHARED_DIR = AGENT_DIR / "capabilities" / "_shared"

sys.path.insert(0, str(INFRA_DIR))
sys.path.insert(0, str(SHARED_DIR))

from figma_mode import detect_mode  # noqa: E402
from figma_models import FigmaMode  # noqa: E402
from figma_mcp_adapter import validate_execution_payload, FigmaMcpBridgeError  # noqa: E402
import design_support  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mode(env: dict[str, str], require_direct: bool = False) -> FigmaMode:
    """Call detect_mode with a patched environment."""
    import unittest.mock as mock
    import os
    with mock.patch.dict(os.environ, env, clear=True):
        with mock.patch("figma_mode.merged_env", return_value=env):
            return detect_mode(Path("/tmp"), require_direct=require_direct)


# ---------------------------------------------------------------------------
# 1. detect_mode — 4 modos
# ---------------------------------------------------------------------------

class TestDetectMode(unittest.TestCase):

    def test_direct_mcp_when_bridge_and_enabled(self):
        mode = _mode({"FIGMA_MCP_BRIDGE_COMMAND": "figma-bridge", "FIGMA_MCP_ENABLED": "true"})
        self.assertEqual(mode.mode, "direct_mcp")

    def test_direct_mcp_via_direct_mode_flag(self):
        mode = _mode({"FIGMA_MCP_BRIDGE_COMMAND": "figma-bridge", "FIGMA_DIRECT_MODE": "1"})
        self.assertEqual(mode.mode, "direct_mcp")

    def test_local_mcp_bridge_when_bridge_only(self):
        mode = _mode({"FIGMA_MCP_BRIDGE_COMMAND": "figma-bridge"})
        self.assertEqual(mode.mode, "local_mcp_bridge")

    def test_plan_only_when_no_bridge(self):
        mode = _mode({})
        self.assertEqual(mode.mode, "plan_only")

    def test_blocked_when_require_direct_and_no_bridge(self):
        mode = _mode({}, require_direct=True)
        self.assertEqual(mode.mode, "blocked")


# ---------------------------------------------------------------------------
# 2. validate_execution_payload — gate de evidencia real
# ---------------------------------------------------------------------------

class TestValidateExecutionPayload(unittest.TestCase):

    def test_passes_with_file_key(self):
        # Should not raise
        validate_execution_payload({"status": "created", "file_key": "abc123"})

    def test_passes_with_node_ids(self):
        validate_execution_payload({"status": "executed", "created_node_ids": ["n1"]})

    def test_passes_with_mutated_node_ids(self):
        validate_execution_payload({"status": "updated", "mutated_node_ids": ["n2"]})

    def test_passes_with_file_url(self):
        validate_execution_payload({"status": "inspected", "file_url": "https://figma.com/f/abc"})

    def test_fails_without_status(self):
        with self.assertRaises(FigmaMcpBridgeError):
            validate_execution_payload({"file_key": "abc"})

    def test_fails_without_evidence(self):
        with self.assertRaises(FigmaMcpBridgeError):
            validate_execution_payload({"status": "created"})

    def test_fails_with_wrong_status(self):
        with self.assertRaises(FigmaMcpBridgeError):
            validate_execution_payload({"status": "pending", "file_key": "abc"})


# ---------------------------------------------------------------------------
# 3. render_azure_context — modo degradado
# ---------------------------------------------------------------------------

class TestRenderAzureContext(unittest.TestCase):

    def _ctx(self, card_id: str = "") -> dict:
        return {
            "azure_card": card_id,
            "brief": "",
            "sources": [],
            "operation": "read-azure-card-for-design",
            "figma_mode": {"mode": "plan_only", "reason": "no bridge"},
            "platform": "web",
            "scope": "fluxo",
            "figma_file_url": None,
            "figma_project_url": None,
            "url": None,
            "target_audience": None,
            "design_style": None,
            "depth": {"level": "light", "reason": "default", "slug": "light"},
            "vendor_skills": [],
            "figma_execution": None,
            "feedback": "",
        }

    def test_degraded_mode_no_card(self):
        ctx = self._ctx("")
        result = design_support.render_azure_context(ctx)
        self.assertIn("Modo Degradado", result)
        self.assertNotIn("sucesso", result)

    def test_degraded_mode_with_card_id_but_no_cli(self):
        """When CLI is unavailable, should fall back to degraded mode."""
        import unittest.mock as mock
        with mock.patch("design_support.delegate_azure_read_card", return_value=None):
            ctx = self._ctx("12345")
            result = design_support.render_azure_context(ctx)
        self.assertIn("12345", result)
        self.assertIn("falhou_modo_degradado", result)

    def test_success_mode_with_delegation_result(self):
        import unittest.mock as mock
        card_data = {"id": "12345", "title": "Login screen"}
        with mock.patch("design_support.delegate_azure_read_card", return_value=card_data):
            ctx = self._ctx("12345")
            result = design_support.render_azure_context(ctx)
        self.assertIn("sucesso", result)
        self.assertIn("Login screen", result)

    def test_does_not_claim_read_without_delegation(self):
        import unittest.mock as mock
        with mock.patch("design_support.delegate_azure_read_card", return_value=None):
            ctx = self._ctx("99")
            result = design_support.render_azure_context(ctx)
        # Must not claim the card was read
        self.assertNotIn("Conteudo do Card (retornado", result)


# ---------------------------------------------------------------------------
# 4. render_documents — artefatos por operacao
# ---------------------------------------------------------------------------

class TestRenderDocuments(unittest.TestCase):

    def _base_context(self, operation: str) -> dict:
        return {
            "operation": operation,
            "title": operation,
            "brief": "Test brief",
            "feedback": "",
            "sources": [],
            "figma_mode": {"mode": "plan_only", "reason": "no bridge"},
            "figma_file_url": None,
            "figma_project_url": None,
            "url": None,
            "azure_card": None,
            "platform": "web",
            "scope": "fluxo",
            "target_audience": None,
            "design_style": None,
            "depth": {"level": "medium", "reason": "default", "slug": "medium"},
            "vendor_skills": [],
            "figma_execution": None,
        }

    def test_conduct_design_interview_produces_brief(self):
        ctx = self._base_context("conduct-design-interview")
        docs = design_support.render_documents(ctx)
        self.assertIn("design-brief.md", docs)
        self.assertIn("open-design-questions.md", docs)

    def test_create_web_app_produces_screen_map(self):
        ctx = self._base_context("create-web-app-design")
        docs = design_support.render_documents(ctx)
        self.assertIn("web-screen-map.md", docs)
        self.assertIn("dev-handoff.md", docs)
        self.assertIn("design-quality-report.md", docs)

    def test_create_mobile_produces_mobile_screen_map(self):
        ctx = self._base_context("create-mobile-app-design")
        ctx["platform"] = "mobile"
        docs = design_support.render_documents(ctx)
        self.assertIn("mobile-screen-map.md", docs)

    def test_read_azure_produces_azure_context(self):
        import unittest.mock as mock
        with mock.patch("design_support.delegate_azure_read_card", return_value=None):
            ctx = self._base_context("read-azure-card-for-design")
            ctx["azure_card"] = "42"
            docs = design_support.render_documents(ctx)
        self.assertIn("azure-card-design-context.md", docs)

    def test_generate_journey_produces_diagram(self):
        ctx = self._base_context("generate-user-journey-diagram")
        docs = design_support.render_documents(ctx)
        self.assertIn("journey-diagram.md", docs)

    def test_all_documents_non_empty(self):
        for op in design_support.CAPABILITY_TITLES:
            with self.subTest(op=op):
                ctx = self._base_context(op)
                docs = design_support.render_documents(ctx)
                for name, content in docs.items():
                    self.assertTrue(content.strip(), f"{op}: {name} is empty")


# ---------------------------------------------------------------------------
# 5. knowledge/system.md existe e nao e vazio
# ---------------------------------------------------------------------------

class TestKnowledgeSystemMd(unittest.TestCase):

    def test_system_md_exists(self):
        path = AGENT_DIR / "knowledge" / "system.md"
        self.assertTrue(path.exists(), "knowledge/system.md nao encontrado")

    def test_system_md_not_empty(self):
        path = AGENT_DIR / "knowledge" / "system.md"
        content = path.read_text(encoding="utf-8").strip()
        self.assertTrue(len(content) > 100, "knowledge/system.md esta vazio ou muito curto")

    def test_system_md_has_required_sections(self):
        path = AGENT_DIR / "knowledge" / "system.md"
        content = path.read_text(encoding="utf-8")
        for section in ["Persona", "Missao", "Escopo", "Guardrails"]:
            self.assertIn(section, content, f"system.md falta secao: {section}")

    def test_system_md_is_first_in_default_context(self):
        import yaml
        agent_yaml = AGENT_DIR / "agent.yaml"
        data = yaml.safe_load(agent_yaml.read_text(encoding="utf-8"))
        ctx = data.get("default_context", [])
        self.assertTrue(len(ctx) > 0, "default_context vazio")
        self.assertEqual(ctx[0], "knowledge/system.md",
                         "knowledge/system.md deve ser o primeiro default_context")


# ---------------------------------------------------------------------------
# 6. workflow.md — nenhum placeholder (todos tem ## OBJETIVO)
# ---------------------------------------------------------------------------

class TestWorkflowMdNotPlaceholder(unittest.TestCase):

    def test_all_workflows_have_objetivo(self):
        caps_dir = AGENT_DIR / "capabilities"
        for cap_dir in sorted(caps_dir.iterdir()):
            if cap_dir.name.startswith("_"):
                continue
            wf = cap_dir / "workflow.md"
            if not wf.exists():
                continue
            content = wf.read_text(encoding="utf-8")
            with self.subTest(capability=cap_dir.name):
                self.assertIn("OBJETIVO", content,
                              f"{cap_dir.name}/workflow.md nao tem secao OBJETIVO")

    def test_all_workflows_have_saida(self):
        caps_dir = AGENT_DIR / "capabilities"
        for cap_dir in sorted(caps_dir.iterdir()):
            if cap_dir.name.startswith("_"):
                continue
            wf = cap_dir / "workflow.md"
            if not wf.exists():
                continue
            content = wf.read_text(encoding="utf-8")
            with self.subTest(capability=cap_dir.name):
                self.assertIn("SAIDA", content,
                              f"{cap_dir.name}/workflow.md nao tem secao SAIDA")


# ---------------------------------------------------------------------------
# 7. knowledge files — os 4 novos existem e sao referenciados
# ---------------------------------------------------------------------------

class TestNewKnowledgeFiles(unittest.TestCase):

    def test_ux_patterns_exists(self):
        self.assertTrue((AGENT_DIR / "knowledge" / "ux-patterns.md").exists())

    def test_accessibility_rules_exists(self):
        self.assertTrue((AGENT_DIR / "knowledge" / "accessibility-rules.md").exists())

    def test_depth_scope_rules_exists(self):
        self.assertTrue((AGENT_DIR / "knowledge" / "depth-scope-rules.md").exists())

    def test_feedback_rubric_exists(self):
        self.assertTrue((AGENT_DIR / "knowledge" / "feedback-rubric.md").exists())

    def test_new_knowledge_in_default_context(self):
        import yaml
        agent_yaml = AGENT_DIR / "agent.yaml"
        data = yaml.safe_load(agent_yaml.read_text(encoding="utf-8"))
        ctx = data.get("default_context", [])
        for kf in ["knowledge/ux-patterns.md", "knowledge/accessibility-rules.md",
                   "knowledge/depth-scope-rules.md", "knowledge/feedback-rubric.md"]:
            self.assertIn(kf, ctx, f"{kf} nao esta em default_context")


if __name__ == "__main__":
    unittest.main()
