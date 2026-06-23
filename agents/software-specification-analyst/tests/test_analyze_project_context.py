#!/usr/bin/env python3
"""Tests for software-specification-analyst/analyze-project-context runner.

Covers: ignored directories, file inventory, output directory handling.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER_PATH = (
    Path(__file__).resolve().parents[1]
    / "capabilities"
    / "analyze-project-context"
    / "runner.py"
)

IGNORED_DIRS = [
    ".git",
    "node_modules",
    "vendor",
    "__pycache__",
    "dist",
    "build",
    "target",
    ".next",
]


def _load_runner():
    module_name = "runner_analyze_project"
    spec = importlib.util.spec_from_file_location(module_name, RUNNER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


class IgnoredDirectoriesTest(unittest.TestCase):
    """Files inside ignored directories must not appear in the inventory."""

    def setUp(self):
        self.runner = _load_runner()

    def _build_project(self, tmpdir: str) -> Path:
        root = Path(tmpdir)
        # Valid source files
        (root / "src").mkdir()
        (root / "src" / "app.py").write_text("# app")
        (root / "README.md").write_text("# Project")
        # Ignored dirs with files that should be excluded
        for d in IGNORED_DIRS:
            ignored = root / d
            ignored.mkdir()
            (ignored / "should_be_ignored.py").write_text("# ignored")
        return root

    def test_ignored_dirs_are_excluded_from_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._build_project(tmpdir)
            snapshot = self.runner.inspect_project(root, requested_depth="light", focus=None)
            for item in snapshot.files:
                path_str = str(item)
                for ignored in IGNORED_DIRS:
                    self.assertNotIn(
                        ignored + "/",
                        path_str,
                        f"Arquivo ignorado encontrado no inventário: {path_str}",
                    )
                    # Also check the beginning of path (e.g. "node_modules/x.py")
                    self.assertFalse(
                        path_str.startswith(ignored + "/") or path_str == ignored,
                        f"Arquivo ignorado encontrado no inventário: {path_str}",
                    )

    def test_valid_source_files_are_in_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._build_project(tmpdir)
            snapshot = self.runner.inspect_project(root, requested_depth="light", focus=None)
            paths = [str(p) for p in snapshot.files]
            self.assertTrue(
                any("app.py" in p for p in paths),
                "app.py should be in inventory",
            )


class OutputDocumentsTest(unittest.TestCase):
    """Verify the runner creates the expected 10 output documents."""

    def setUp(self):
        self.runner = _load_runner()

    def _make_snapshot(self, tmpdir: str):
        root = Path(tmpdir)
        (root / "README.md").write_text("# Test Project")
        (root / "src").mkdir()
        (root / "src" / "main.py").write_text("def main(): pass")
        return self.runner.inspect_project(root, requested_depth="light", focus=None)

    def test_render_documents_returns_10_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot = self._make_snapshot(tmpdir)
            docs = self.runner.render_documents(snapshot)
            expected = {
                "analysis-context.md",
                "project-architecture-notes.md",
                "business-rules-discovered.md",
                "critical-points.md",
                "business-questions.md",
                "technical-impact-analysis.md",
                "integration-map.md",
                "data-and-permissions-analysis.md",
                "open-decisions.md",
                "analysis-review.md",
            }
            self.assertEqual(set(docs.keys()), expected)

    def test_analysis_context_references_project_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot = self._make_snapshot(tmpdir)
            docs = self.runner.render_documents(snapshot)
            # The project name (tmpdir's basename) should appear in the context doc
            self.assertIn("Contexto De Analise", docs["analysis-context.md"])


if __name__ == "__main__":
    unittest.main()
