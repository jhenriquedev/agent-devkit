"""Tests for source_reader.py — multi-format ingestion."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

DRAWIO_DIR = Path(__file__).resolve().parents[1] / "infra" / "integrations" / "drawio"
sys.path.insert(0, str(DRAWIO_DIR))

from source_reader import load_sources  # noqa: E402


class TestLoadSources(unittest.TestCase):
    def test_load_from_text(self):
        result = load_sources(text="The system authenticates the user via OAuth.")
        self.assertIn("combined_text", result)
        self.assertIn("sources", result)
        self.assertGreater(result["source_count"], 0)

    def test_load_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# System\n\nThe API Gateway routes requests to microservices.\n")
            path = f.name
        result = load_sources(files=[path])
        self.assertIn("combined_text", result)
        self.assertIn("API Gateway", result["combined_text"])

    def test_load_from_json_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({"component": "Auth Service", "action": "validates tokens"}, f)
            path = f.name
        result = load_sources(files=[path])
        self.assertIn("combined_text", result)
        self.assertGreater(len(result["combined_text"]), 0)

    def test_failed_sources_recorded(self):
        result = load_sources(files=["/nonexistent/path/file.md"])
        self.assertIn("failed_sources", result)
        self.assertEqual(len(result["failed_sources"]), 1)

    def test_no_sources_returns_empty(self):
        result = load_sources()
        self.assertIn("source_count", result)
        self.assertEqual(result["source_count"], 0)

    def test_combined_text_from_multiple_sources(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f1:
            f1.write("Component A calls Component B.")
            path1 = f1.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f2:
            f2.write("Component B responds to Component A.")
            path2 = f2.name
        result = load_sources(files=[path1, path2])
        self.assertGreater(result["source_count"], 1)
        self.assertIn("Component A", result["combined_text"])
        self.assertIn("Component B", result["combined_text"])


if __name__ == "__main__":
    unittest.main()
