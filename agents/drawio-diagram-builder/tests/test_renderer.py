"""Tests for drawio_renderer.py — renderer, shape library, style presets, layout."""

import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree

DRAWIO_DIR = Path(__file__).resolve().parents[1] / "infra" / "integrations" / "drawio"
sys.path.insert(0, str(DRAWIO_DIR))

from drawio_renderer import (  # noqa: E402
    render_drawio,
    slug,
    compact_label,
    split_statements,
    infer_title,
    _get_shape_library,
    _get_style_preset,
    _diagram_family,
    recommend_layout,
)


MINIMAL_SPEC = {
    "title": "Test Diagram",
    "diagram_type": "flowchart",
    "nodes": [
        {"id": "n1", "label": "Step One", "group": "Fluxo", "kind": "process"},
        {"id": "n2", "label": "Step Two", "group": "Fluxo", "kind": "decision"},
    ],
    "edges": [{"source": "n1", "target": "n2", "label": "proximo"}],
}


class TestRenderDrawio(unittest.TestCase):
    def test_renders_valid_xml(self):
        xml = render_drawio(MINIMAL_SPEC)
        self.assertIsInstance(xml, str)
        root = ElementTree.fromstring(xml)
        self.assertEqual(root.tag, "mxfile")

    def test_has_root_mxfile(self):
        xml = render_drawio(MINIMAL_SPEC)
        root = ElementTree.fromstring(xml)
        self.assertEqual(root.tag, "mxfile")

    def test_has_diagram_title_cell(self):
        xml = render_drawio(MINIMAL_SPEC)
        root = ElementTree.fromstring(xml)
        title_cell = root.find(".//mxCell[@id='diagram-title']")
        self.assertIsNotNone(title_cell)
        self.assertEqual(title_cell.get("value"), "Test Diagram")

    def test_has_nodes(self):
        xml = render_drawio(MINIMAL_SPEC)
        root = ElementTree.fromstring(xml)
        n1_id = "node-" + slug("n1")
        n1 = root.find(f".//mxCell[@id='{n1_id}']")
        self.assertIsNotNone(n1)

    def test_has_edge(self):
        xml = render_drawio(MINIMAL_SPEC)
        root = ElementTree.fromstring(xml)
        edge = root.find(".//mxCell[@id='edge-1']")
        self.assertIsNotNone(edge)
        self.assertEqual(edge.get("value"), "proximo")

    def test_empty_nodes_fallback(self):
        spec = {"title": "Empty", "diagram_type": "flowchart", "nodes": [], "edges": []}
        xml = render_drawio(spec)
        root = ElementTree.fromstring(xml)
        self.assertEqual(root.tag, "mxfile")

    def test_architecture_preset_applied(self):
        spec = {
            "title": "Arch",
            "diagram_type": "architecture",
            "nodes": [{"id": "svc", "label": "Service", "kind": "system"}],
            "edges": [],
        }
        xml = render_drawio(spec)
        root = ElementTree.fromstring(xml)
        svc_id = "node-" + slug("svc")
        node_cell = root.find(f".//mxCell[@id='{svc_id}']")
        self.assertIsNotNone(node_cell)
        # architecture preset uses purple-ish fill
        style = node_cell.get("style", "")
        self.assertIn("e1d5e7", style)

    def test_data_preset_for_erd(self):
        spec = {
            "title": "ERD",
            "diagram_type": "erd",
            "nodes": [{"id": "t1", "label": "Table One", "kind": "entity"}],
            "edges": [],
        }
        xml = render_drawio(spec)
        root = ElementTree.fromstring(xml)
        t1_id = "node-" + slug("t1")
        node_cell = root.find(f".//mxCell[@id='{t1_id}']")
        self.assertIsNotNone(node_cell)
        style = node_cell.get("style", "")
        # data preset: f8cecc fill
        self.assertIn("f8cecc", style)

    def test_split_recommended_annotation_in_legend(self):
        """Diagrams with > 12 nodes should show split recommendation in legend."""
        nodes = [{"id": f"n{i}", "label": f"Step {i}", "kind": "process"} for i in range(14)]
        spec = {"title": "Dense", "diagram_type": "flowchart", "nodes": nodes, "edges": []}
        xml = render_drawio(spec)
        self.assertIn("considere dividir", xml)


class TestShapeLibrary(unittest.TestCase):
    def test_shape_library_loads(self):
        shapes = _get_shape_library()
        self.assertIsInstance(shapes, dict)

    def test_shape_library_has_known_kinds(self):
        shapes = _get_shape_library()
        if shapes:
            self.assertIn("process", shapes)
            self.assertIn("decision", shapes)
            self.assertIn("database", shapes)
            self.assertIn("actor", shapes)

    def test_shape_library_used_in_render(self):
        """Node style should come from shape-library.yaml when available."""
        shapes = _get_shape_library()
        if not shapes or "decision" not in shapes:
            self.skipTest("shape-library.yaml not available or missing decision")
        spec = {
            "title": "ShapeTest",
            "diagram_type": "flowchart",
            "nodes": [{"id": "d1", "label": "Decide", "kind": "decision"}],
            "edges": [],
        }
        xml = render_drawio(spec)
        root = ElementTree.fromstring(xml)
        d1_id = "node-" + slug("d1")
        node_cell = root.find(f".//mxCell[@id='{d1_id}']")
        self.assertIsNotNone(node_cell)
        # decision kind should produce rhombus shape
        self.assertIn("rhombus", node_cell.get("style", ""))


class TestStylePresets(unittest.TestCase):
    def test_style_presets_loads(self):
        preset = _get_style_preset("architecture")
        self.assertIsInstance(preset, dict)

    def test_style_presets_has_expected_families(self):
        for family in ("architecture", "product", "data", "default"):
            preset = _get_style_preset(family)
            self.assertIsInstance(preset, dict)
            if preset:
                self.assertIn("node_fill", preset)

    def test_unknown_family_falls_back_to_default(self):
        preset = _get_style_preset("unknown_family_xyz")
        default = _get_style_preset("default")
        self.assertEqual(preset, default)


class TestLayoutEngine(unittest.TestCase):
    def test_recommend_layout_flow(self):
        result = recommend_layout("flowchart", 5)
        self.assertIn("direction", result)
        self.assertEqual(result["split_recommended"], False)

    def test_recommend_layout_erd_top_to_bottom(self):
        result = recommend_layout("erd", 3)
        self.assertEqual(result["direction"], "top-to-bottom")

    def test_recommend_layout_split_recommended(self):
        result = recommend_layout("flowchart", 15)
        self.assertTrue(result["split_recommended"])

    def test_diagram_family_mapping(self):
        self.assertEqual(_diagram_family("architecture"), "architecture")
        self.assertEqual(_diagram_family("erd"), "data")
        self.assertEqual(_diagram_family("flowchart"), "product")
        self.assertIsNone(_diagram_family(None))


class TestHelpers(unittest.TestCase):
    def test_slug(self):
        # slug strips trailing separators
        self.assertEqual(slug("Hello World!"), "Hello-World")
        self.assertEqual(slug(""), "item")

    def test_compact_label(self):
        label = compact_label("This is a very long statement that should be truncated")
        self.assertLessEqual(len(label), 48)

    def test_split_statements(self):
        text = "Step one. Step two. Step three."
        parts = split_statements(text)
        self.assertGreaterEqual(len(parts), 2)

    def test_infer_title(self):
        title = infer_title("The system authenticates the user", "flowchart")
        self.assertIsInstance(title, str)
        self.assertGreater(len(title), 0)


if __name__ == "__main__":
    unittest.main()
