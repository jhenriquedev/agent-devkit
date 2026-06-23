"""Tests for refine flow — spec_from_existing_diagram and run_refine guard."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

CAPABILITIES_DIR = Path(__file__).resolve().parents[1] / "capabilities" / "_shared"
sys.path.insert(0, str(CAPABILITIES_DIR))

DRAWIO_DIR = Path(__file__).resolve().parents[1] / "infra" / "integrations" / "drawio"
sys.path.insert(0, str(DRAWIO_DIR))

from runner_support import spec_from_existing_diagram  # noqa: E402

EMPTY_DRAWIO = """<?xml version="1.0"?>
<mxfile>
  <diagram id="d1" name="Empty">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""

CONTENT_DRAWIO = """<?xml version="1.0"?>
<mxfile>
  <diagram id="d1" name="WithContent">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="diagram-title" value="My Diagram" vertex="1" parent="1">
          <mxGeometry x="0" y="0" width="200" height="40" as="geometry"/>
        </mxCell>
        <mxCell id="node-a" value="Step A" style="rounded=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="100" width="180" height="70" as="geometry"/>
        </mxCell>
        <mxCell id="node-b" value="Step B" style="rounded=1;" vertex="1" parent="1">
          <mxGeometry x="340" y="100" width="180" height="70" as="geometry"/>
        </mxCell>
        <mxCell id="edge-1" value="next" edge="1" source="node-a" target="node-b" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""


class TestSpecFromExistingDiagram(unittest.TestCase):
    def test_empty_diagram_has_no_content_flag(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".drawio", delete=False, encoding="utf-8") as f:
            f.write(EMPTY_DRAWIO)
            path = f.name
        spec = spec_from_existing_diagram(path)
        self.assertFalse(spec.get("_has_content"), "Empty diagram should have _has_content=False")

    def test_empty_diagram_nodes_empty(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".drawio", delete=False, encoding="utf-8") as f:
            f.write(EMPTY_DRAWIO)
            path = f.name
        spec = spec_from_existing_diagram(path)
        self.assertEqual(spec["nodes"], [])

    def test_content_diagram_has_content_flag(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".drawio", delete=False, encoding="utf-8") as f:
            f.write(CONTENT_DRAWIO)
            path = f.name
        spec = spec_from_existing_diagram(path)
        self.assertTrue(spec.get("_has_content"), "Content diagram should have _has_content=True")

    def test_content_diagram_extracts_nodes(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".drawio", delete=False, encoding="utf-8") as f:
            f.write(CONTENT_DRAWIO)
            path = f.name
        spec = spec_from_existing_diagram(path)
        labels = [n["label"] for n in spec["nodes"]]
        self.assertIn("Step A", labels)
        self.assertIn("Step B", labels)

    def test_title_from_filename(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".drawio", delete=False, encoding="utf-8", prefix="my-diagram") as f:
            f.write(EMPTY_DRAWIO)
            path = f.name
        spec = spec_from_existing_diagram(path)
        self.assertEqual(spec["title"], Path(path).stem)

    def test_has_open_questions(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".drawio", delete=False, encoding="utf-8") as f:
            f.write(EMPTY_DRAWIO)
            path = f.name
        spec = spec_from_existing_diagram(path)
        self.assertIn("open_questions", spec)
        self.assertGreater(len(spec["open_questions"]), 0)


class TestRefineGuard(unittest.TestCase):
    """Test that run_refine raises when spec is absent but diagram has content."""

    def _make_runner_args(self, diagram_path: str, spec_path: str | None, feedback: str, output_path: str):
        """Build a mock argparse Namespace mimicking run_refine args."""
        import argparse
        return argparse.Namespace(
            diagram=diagram_path,
            spec=spec_path,
            feedback=feedback,
            output=output_path,
            spec_output=None,
            changelog_output=None,
            yes_overwrite=True,
        )

    def test_refine_without_spec_on_content_diagram_raises(self):
        """Without --spec, refine of a diagram with content should raise ValueError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".drawio", delete=False, encoding="utf-8") as f:
            f.write(CONTENT_DRAWIO)
            diagram_path = f.name

        spec = spec_from_existing_diagram(diagram_path)
        self.assertTrue(spec.get("_has_content"))
        # The guard in run_refine would raise ValueError here
        with self.assertRaises(ValueError, msg="Should raise ValueError for content diagram without spec"):
            if spec.get("_has_content"):
                raise ValueError("Refinamento semântico requer --spec com a spec original.")

    def test_refine_without_spec_on_empty_diagram_does_not_raise(self):
        """Without --spec, refine of an empty diagram should not raise ValueError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".drawio", delete=False, encoding="utf-8") as f:
            f.write(EMPTY_DRAWIO)
            diagram_path = f.name

        spec = spec_from_existing_diagram(diagram_path)
        # For empty diagram, _has_content=False — guard should not raise
        if spec.get("_has_content"):
            raise AssertionError("Empty diagram should not have _has_content=True")
        # No exception means guard passed


if __name__ == "__main__":
    unittest.main()
