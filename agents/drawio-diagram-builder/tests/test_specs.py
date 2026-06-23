"""Tests for spec_builder.py — ERD, architecture, flow specs."""

import sys
import unittest
from pathlib import Path

DRAWIO_DIR = Path(__file__).resolve().parents[1] / "infra" / "integrations" / "drawio"
sys.path.insert(0, str(DRAWIO_DIR))

from spec_builder import (  # noqa: E402
    build_specialized_spec,
    build_erd_spec,
    build_architecture_spec,
    build_flow_spec,
    apply_feedback_to_spec,
)


ERD_TEXT = """
Tabela Usuario possui id, nome, email, perfil_id.
Tabela Perfil possui id, nome, permissoes.
Usuario pertence a Perfil.
"""

ARCH_TEXT = """
O cliente acessa o API Gateway.
O API Gateway chama o Auth Service.
O Auth Service consulta o banco de dados PostgreSQL.
"""

FLOW_TEXT = """
O usuario faz login.
O sistema valida a senha.
Se a senha estiver correta, o sistema emite o token.
Caso contrario, o sistema exibe mensagem de erro.
"""


class TestBuildErdSpec(unittest.TestCase):
    def test_detects_entities(self):
        spec = build_erd_spec(ERD_TEXT)
        ids = [n["id"] for n in spec["nodes"]]
        self.assertIn("usuario", ids)
        self.assertIn("perfil", ids)

    def test_diagram_type_is_erd(self):
        spec = build_erd_spec(ERD_TEXT)
        self.assertEqual(spec["diagram_type"], "erd")

    def test_all_nodes_have_id_and_label(self):
        spec = build_erd_spec(ERD_TEXT)
        for node in spec["nodes"]:
            self.assertIn("id", node)
            self.assertIn("label", node)

    def test_relationship_edge_detected(self):
        spec = build_erd_spec(ERD_TEXT)
        edge_pairs = [(e["source"], e["target"]) for e in spec.get("edges", [])]
        # usuario pertence a perfil
        self.assertTrue(
            any(src == "usuario" and tgt == "perfil" for src, tgt in edge_pairs),
            f"Expected usuario->perfil edge, got: {edge_pairs}"
        )

    def test_has_facts(self):
        spec = build_erd_spec(ERD_TEXT)
        self.assertIsInstance(spec.get("facts"), list)
        self.assertGreater(len(spec["facts"]), 0)


class TestBuildArchitectureSpec(unittest.TestCase):
    def test_detects_components(self):
        spec = build_architecture_spec(ARCH_TEXT)
        labels = [n["label"].lower() for n in spec["nodes"]]
        self.assertTrue(any("gateway" in l or "api" in l for l in labels))

    def test_diagram_type_is_architecture(self):
        spec = build_architecture_spec(ARCH_TEXT)
        self.assertEqual(spec["diagram_type"], "architecture")

    def test_edges_have_labels(self):
        spec = build_architecture_spec(ARCH_TEXT)
        for edge in spec.get("edges", []):
            self.assertIn("label", edge)
            self.assertTrue(len(edge["label"]) > 0)

    def test_all_nodes_have_id_and_label(self):
        spec = build_architecture_spec(ARCH_TEXT)
        for node in spec["nodes"]:
            self.assertIn("id", node)
            self.assertIn("label", node)


class TestBuildFlowSpec(unittest.TestCase):
    def test_has_nodes(self):
        spec = build_flow_spec(FLOW_TEXT)
        self.assertGreater(len(spec["nodes"]), 0)

    def test_diagram_type_is_flowchart(self):
        spec = build_flow_spec(FLOW_TEXT)
        self.assertEqual(spec["diagram_type"], "flowchart")

    def test_decision_kind_detected(self):
        spec = build_flow_spec(FLOW_TEXT)
        kinds = [n.get("kind") for n in spec["nodes"]]
        self.assertIn("decision", kinds)

    def test_edges_connect_sequential_nodes(self):
        spec = build_flow_spec(FLOW_TEXT)
        node_ids = {n["id"] for n in spec["nodes"]}
        for edge in spec.get("edges", []):
            self.assertIn(edge["source"], node_ids)
            self.assertIn(edge["target"], node_ids)


class TestBuildSpecializedSpec(unittest.TestCase):
    def test_routes_erd(self):
        spec = build_specialized_spec(ERD_TEXT, diagram_type="erd")
        self.assertEqual(spec["diagram_type"], "erd")

    def test_routes_architecture(self):
        spec = build_specialized_spec(ARCH_TEXT, diagram_type="architecture")
        self.assertEqual(spec["diagram_type"], "architecture")

    def test_routes_flowchart(self):
        spec = build_specialized_spec(FLOW_TEXT, diagram_type="flowchart")
        self.assertEqual(spec["diagram_type"], "flowchart")

    def test_fallback_for_unknown_type(self):
        spec = build_specialized_spec("Some text about a system.", diagram_type="unknown_type")
        self.assertIn("nodes", spec)

    def test_uses_provided_title(self):
        spec = build_specialized_spec("Some text.", diagram_type="flowchart", title="My Custom Title")
        self.assertEqual(spec["title"], "My Custom Title")


class TestApplyFeedbackToSpec(unittest.TestCase):
    BASE_SPEC = {
        "title": "Test",
        "diagram_type": "flowchart",
        "nodes": [
            {"id": "n1", "label": "Step One", "kind": "process"},
            {"id": "n2", "label": "Step Two", "kind": "process"},
        ],
        "edges": [{"source": "n1", "target": "n2", "label": "next"}],
    }

    def test_rename_node(self):
        spec, changes = apply_feedback_to_spec(self.BASE_SPEC, "renomeie Step One para Inicio")
        labels = [n["label"] for n in spec["nodes"]]
        self.assertIn("Inicio", labels)
        self.assertNotIn("Step One", labels)
        self.assertTrue(any("Renomeado" in c for c in changes))

    def test_add_node(self):
        spec, changes = apply_feedback_to_spec(self.BASE_SPEC, "adicione Fim")
        labels = [n["label"] for n in spec["nodes"]]
        self.assertIn("Fim", labels)
        self.assertTrue(any("Adicionado" in c for c in changes))

    def test_remove_node(self):
        spec, changes = apply_feedback_to_spec(self.BASE_SPEC, "remova Step Two")
        labels = [n["label"] for n in spec["nodes"]]
        self.assertNotIn("Step Two", labels)
        self.assertTrue(any("Removido" in c for c in changes))

    def test_remove_node_removes_dangling_edges(self):
        spec, _ = apply_feedback_to_spec(self.BASE_SPEC, "remova Step Two")
        node_ids = {n["id"] for n in spec["nodes"]}
        for edge in spec.get("edges", []):
            self.assertIn(edge["source"], node_ids)
            self.assertIn(edge["target"], node_ids)

    def test_unknown_feedback_recorded_as_note(self):
        spec, changes = apply_feedback_to_spec(self.BASE_SPEC, "faça algo não mapeado aqui")
        self.assertTrue(any("nota" in c.lower() or "registrado" in c.lower() for c in changes))
        self.assertIn("refinement_notes", spec)

    def test_spec_is_deep_copy(self):
        """Original spec must not be mutated."""
        original_labels = [n["label"] for n in self.BASE_SPEC["nodes"]]
        apply_feedback_to_spec(self.BASE_SPEC, "renomeie Step One para X")
        labels_after = [n["label"] for n in self.BASE_SPEC["nodes"]]
        self.assertEqual(original_labels, labels_after)


if __name__ == "__main__":
    unittest.main()
