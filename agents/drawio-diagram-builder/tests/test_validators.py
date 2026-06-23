"""Tests for validators.py — quality gates and schema validation."""

import sys
import unittest
from pathlib import Path

DRAWIO_DIR = Path(__file__).resolve().parents[1] / "infra" / "integrations" / "drawio"
sys.path.insert(0, str(DRAWIO_DIR))

from validators import validate_drawio_text, render_review, validate_spec_against_schema  # noqa: E402

VALID_DRAWIO = """<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="AI DevKit" agent="drawio-diagram-builder">
  <diagram id="diagram-1" name="Test">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="diagram-title" value="Test Diagram" style="text;" vertex="1" parent="1">
          <mxGeometry x="40" y="20" width="200" height="40" as="geometry"/>
        </mxCell>
        <mxCell id="node-n1" value="Step One" style="rounded=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="100" width="180" height="70" as="geometry"/>
        </mxCell>
        <mxCell id="node-n2" value="Step Two" style="rounded=1;" vertex="1" parent="1">
          <mxGeometry x="340" y="100" width="180" height="70" as="geometry"/>
        </mxCell>
        <mxCell id="edge-1" value="next" style="endArrow=block;" edge="1" source="node-n1" target="node-n2" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""

INVALID_XML = "this is not xml at all"

MISSING_MXFILE_ROOT = """<?xml version="1.0"?>
<wrongroot><diagram id="x" name="x"><mxGraphModel><root><mxCell id="0"/></root></mxGraphModel></diagram></wrongroot>"""

NODE_MISSING_LABEL = """<?xml version="1.0"?>
<mxfile>
  <diagram id="x" name="x">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="diagram-title" value="T" vertex="1" parent="1">
          <mxGeometry x="0" y="0" width="100" height="40" as="geometry"/>
        </mxCell>
        <mxCell id="node-bad" value="" style="rounded=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="100" width="180" height="70" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""

EDGE_DANGLING = """<?xml version="1.0"?>
<mxfile>
  <diagram id="x" name="x">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="diagram-title" value="T" vertex="1" parent="1">
          <mxGeometry x="0" y="0" width="100" height="40" as="geometry"/>
        </mxCell>
        <mxCell id="node-a" value="A" style="rounded=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="100" width="180" height="70" as="geometry"/>
        </mxCell>
        <mxCell id="edge-1" value="x" style="endArrow=block;" edge="1" source="node-a" target="node-nonexistent" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""


class TestValidateDrawioText(unittest.TestCase):
    def test_valid_diagram(self):
        result = validate_drawio_text(VALID_DRAWIO)
        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])

    def test_invalid_xml(self):
        result = validate_drawio_text(INVALID_XML)
        self.assertFalse(result["valid"])
        self.assertTrue(any("XML" in e or "invalido" in e.lower() for e in result["errors"]))

    def test_missing_mxfile_root(self):
        result = validate_drawio_text(MISSING_MXFILE_ROOT)
        self.assertFalse(result["valid"])
        self.assertTrue(any("mxfile" in e.lower() for e in result["errors"]))

    def test_node_missing_label(self):
        result = validate_drawio_text(NODE_MISSING_LABEL)
        self.assertFalse(result["valid"])
        self.assertTrue(any("label" in e.lower() or "sem label" in e.lower() for e in result["errors"]))

    def test_dangling_edge(self):
        result = validate_drawio_text(EDGE_DANGLING)
        self.assertFalse(result["valid"])
        self.assertTrue(any("inexistente" in e or "target" in e.lower() for e in result["errors"]))

    def test_gate_status_ok_for_valid(self):
        result = validate_drawio_text(VALID_DRAWIO)
        gates = result.get("gate_status", {})
        self.assertEqual(gates.get("xml_parseavel"), "ok")
        self.assertEqual(gates.get("raiz_mxfile_presente"), "ok")
        self.assertEqual(gates.get("nos_com_labels"), "ok")

    def test_node_count(self):
        result = validate_drawio_text(VALID_DRAWIO)
        self.assertEqual(result["node_count"], 2)

    def test_edge_count(self):
        result = validate_drawio_text(VALID_DRAWIO)
        self.assertEqual(result["edge_count"], 1)


class TestRenderReview(unittest.TestCase):
    def test_renders_markdown(self):
        result = validate_drawio_text(VALID_DRAWIO)
        review = render_review(result)
        self.assertIn("# Draw.io Diagram Review", review)
        self.assertIn("Quality Gates", review)

    def test_errors_section_present(self):
        result = validate_drawio_text(INVALID_XML)
        review = render_review(result)
        self.assertIn("Erros", review)

    def test_valid_shows_no_errors(self):
        result = validate_drawio_text(VALID_DRAWIO)
        review = render_review(result)
        self.assertIn("Nenhum erro bloqueante", review)


class TestValidateSpecAgainstSchema(unittest.TestCase):
    def test_valid_spec(self):
        spec = {
            "title": "My Diagram",
            "diagram_type": "flowchart",
            "nodes": [{"id": "n1", "label": "Step One"}],
            "edges": [{"source": "n1", "target": "n1", "label": "loop"}],
        }
        errors = validate_spec_against_schema(spec)
        self.assertEqual(errors, [])

    def test_missing_title(self):
        spec = {"diagram_type": "flowchart", "nodes": []}
        errors = validate_spec_against_schema(spec)
        self.assertTrue(any("title" in e for e in errors))

    def test_missing_nodes(self):
        spec = {"title": "T", "diagram_type": "flowchart"}
        errors = validate_spec_against_schema(spec)
        self.assertTrue(any("nodes" in e for e in errors))

    def test_node_missing_id(self):
        spec = {"title": "T", "diagram_type": "flowchart", "nodes": [{"label": "X"}]}
        errors = validate_spec_against_schema(spec)
        self.assertTrue(any("id" in e for e in errors))

    def test_node_missing_label(self):
        spec = {"title": "T", "diagram_type": "flowchart", "nodes": [{"id": "n1"}]}
        errors = validate_spec_against_schema(spec)
        self.assertTrue(any("label" in e for e in errors))

    def test_edge_dangling_source(self):
        spec = {
            "title": "T",
            "diagram_type": "flowchart",
            "nodes": [{"id": "n1", "label": "Node"}],
            "edges": [{"source": "nonexistent", "target": "n1"}],
        }
        errors = validate_spec_against_schema(spec)
        self.assertTrue(any("source" in e and "nonexistent" in e for e in errors))

    def test_edge_dangling_target(self):
        spec = {
            "title": "T",
            "diagram_type": "flowchart",
            "nodes": [{"id": "n1", "label": "Node"}],
            "edges": [{"source": "n1", "target": "ghost"}],
        }
        errors = validate_spec_against_schema(spec)
        self.assertTrue(any("target" in e and "ghost" in e for e in errors))

    def test_not_dict(self):
        errors = validate_spec_against_schema([])  # type: ignore
        self.assertTrue(any("objeto" in e.lower() for e in errors))


if __name__ == "__main__":
    unittest.main()
