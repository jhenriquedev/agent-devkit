#!/usr/bin/env python3
"""Tests for software-specification-analyst/create-final-spec-from-analysis runner.

Covers: Handoff Para Desenvolvimento presence, open-questions artifact,
7 artefatos gerados, leitura de analysis_dir.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


RUNNER_PATH = (
    Path(__file__).resolve().parents[1]
    / "capabilities"
    / "create-final-spec-from-analysis"
    / "runner.py"
)


def _load_runner():
    spec = importlib.util.spec_from_file_location("runner_final_spec", RUNNER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FinalSpecArtifactsTest(unittest.TestCase):
    def setUp(self):
        self.runner = _load_runner()

    def _make_context(self, title="Spec Final Teste"):
        return {
            "title": title,
            "analysis": "# Análise\n\nFATO OBSERVADO: sistema usa Django.",
            "decisions": ["Usar autenticação JWT", "Manter banco PostgreSQL"],
            "questions": ["Qual o SLA esperado?", "Há auditoria obrigatória?"],
        }

    def test_render_documents_returns_7_artifacts(self):
        ctx = self._make_context()
        docs = self.runner.render_documents(ctx["title"], ctx["analysis"])
        expected = {
            "software-specification.md",
            "functional-spec.md",
            "technical-spec.md",
            "user-stories.md",
            "journey-flows.md",
            "requirements-traceability.md",
            "open-questions.md",
        }
        self.assertEqual(set(docs.keys()), expected)

    def test_software_spec_has_handoff_para_desenvolvimento(self):
        ctx = self._make_context()
        docs = self.runner.render_documents(ctx["title"], ctx["analysis"])
        spec = docs["software-specification.md"]
        self.assertIn("## Handoff Para Desenvolvimento", spec)

    def test_open_questions_artifact_is_generated(self):
        ctx = self._make_context()
        docs = self.runner.render_documents(ctx["title"], ctx["analysis"])
        self.assertIn("open-questions.md", docs)
        self.assertTrue(len(docs["open-questions.md"]) > 0)

    def test_read_markdown_dir_concatenates_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            (p / "refined-analysis.md").write_text("# Análise Refinada\n\nConteúdo.")
            (p / "decision-log.md").write_text("# Decisões\n\n- Decisão A")
            result = self.runner.read_markdown_dir(p)
            self.assertIn("Análise Refinada", result)
            self.assertIn("Decisão A", result)

    def test_extract_questions_finds_question_marks(self):
        text = "- Qual é o SLA?\n- Este é um fato.\n- Há auditoria?"
        questions = self.runner.extract_questions(text)
        self.assertIn("Qual é o SLA?", questions)
        self.assertIn("Há auditoria?", questions)
        self.assertNotIn("Este é um fato.", questions)


class FinalSpecWritePolicyTest(unittest.TestCase):
    """Verify output dir creation respects write policy (ask_before_creating)."""

    def setUp(self):
        self.runner = _load_runner()

    def test_ensure_output_dir_creates_when_yes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "final" / "spec"
            self.runner.ensure_output_dir(target, yes_create_dir=True)
            self.assertTrue(target.exists())

    def test_ensure_output_dir_rejects_when_user_says_no(self):
        import unittest.mock as mock
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "new-spec"
            with mock.patch("builtins.input", return_value="N"):
                with self.assertRaises(ValueError):
                    self.runner.ensure_output_dir(target, yes_create_dir=False)


if __name__ == "__main__":
    unittest.main()
