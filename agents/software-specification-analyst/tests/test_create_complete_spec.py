#!/usr/bin/env python3
"""Tests for software-specification-analyst/create-complete-spec runner.

Covers: slug generation, output directory creation/rejection, overwrite guard,
and conformidade das 21 seções de specification_policy.
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
    / "create-complete-spec"
    / "runner.py"
)

# Required sections from specification_policy (21 seções)
REQUIRED_SECTIONS = [
    "Resumo Executivo",
    "Contexto E Problema",
    "Objetivos",
    "Escopo",
    "Fora De Escopo",
    "Atores E Personas",
    "Requisitos Funcionais",
    "Requisitos Nao Funcionais",
    "Regras De Negocio",
    "User Stories",
    "Criterios De Aceite",
    "Jornadas E Fluxogramas",
    "Modelo De Dados",
    "APIs E Integracoes",
    "Permissoes E Seguranca",
    "Observabilidade",
    "Estrategia De Testes",
    "Riscos E Dependencias",
    "Matriz De Rastreabilidade",
    "Perguntas Abertas",
    "Handoff Para Desenvolvimento",
]


def _load_runner():
    """Dynamically load the runner module."""
    module_name = "runner_complete_spec"
    spec = importlib.util.spec_from_file_location(module_name, RUNNER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


class SlugTest(unittest.TestCase):
    def setUp(self):
        self.runner = _load_runner()

    def test_slug_basic(self):
        self.assertEqual(self.runner.slugify("Minha Especificação"), "minha-especificacao")

    def test_slug_strips_special_chars(self):
        result = self.runner.slugify("Cadastro de Usuário v2")
        self.assertRegex(result, r"^[a-z0-9\-]+$")

    def test_slug_fallback_when_empty(self):
        self.assertEqual(self.runner.slugify(""), "software-specification")

    def test_slug_no_trailing_hyphens(self):
        result = self.runner.slugify("---test---")
        self.assertFalse(result.startswith("-"))
        self.assertFalse(result.endswith("-"))


class TitleInferenceTest(unittest.TestCase):
    def setUp(self):
        self.runner = _load_runner()

    def test_infers_title_from_h1(self):
        text = "# Meu Projeto\n\nconteúdo"
        title = self.runner.infer_title(text, Path("fallback.md"))
        self.assertEqual(title, "Meu Projeto")

    def test_infers_title_from_first_line(self):
        text = "Projeto de integração\n\ndetalhes"
        title = self.runner.infer_title(text, Path("fallback.md"))
        self.assertEqual(title, "Projeto de integração")

    def test_infers_title_from_fallback_path(self):
        title = self.runner.infer_title("", Path("meu-projeto.md"))
        self.assertEqual(title, "Meu Projeto")


class OutputDirTest(unittest.TestCase):
    def setUp(self):
        self.runner = _load_runner()

    def test_resolve_output_dir_uses_slug_under_specifications(self):
        result = self.runner.resolve_output_dir(None, "meu-projeto")
        self.assertIn("specifications", str(result))
        self.assertIn("meu-projeto", str(result))

    def test_resolve_output_dir_respects_explicit_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.resolve_output_dir(tmpdir, "slug")
            self.assertEqual(str(result), str(Path(tmpdir).expanduser().resolve()))

    def test_ensure_output_dir_creates_when_yes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "specs" / "my-spec"
            self.runner.ensure_output_dir(target, yes_create_dir=True)
            self.assertTrue(target.exists())

    def test_ensure_output_dir_raises_on_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "not-a-dir.md"
            file_path.write_text("x")
            with self.assertRaises(ValueError):
                self.runner.ensure_output_dir(file_path, yes_create_dir=True)

    def test_ensure_output_dir_ok_when_already_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            existing = Path(tmpdir)
            # Should not raise
            self.runner.ensure_output_dir(existing, yes_create_dir=True)


class OverwriteGuardTest(unittest.TestCase):
    def setUp(self):
        self.runner = _load_runner()

    def test_write_documents_creates_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            docs = {"spec.md": "# Test\n\nContent"}
            self.runner.write_documents(out, docs, yes_overwrite=True)
            self.assertTrue((out / "spec.md").exists())
            self.assertIn("Content", (out / "spec.md").read_text())

    def test_write_documents_raises_on_existing_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            (out / "spec.md").write_text("original")
            docs = {"spec.md": "new content"}
            # Without --yes-overwrite and no stdin, should raise ValueError
            # We patch by providing a mock that simulates "N" response
            import unittest.mock as mock
            with mock.patch("builtins.input", return_value="N"):
                with self.assertRaises(ValueError):
                    self.runner.write_documents(out, docs, yes_overwrite=False)


class SpecSectionsTest(unittest.TestCase):
    """Verify render_complete_spec emits all 21 required sections."""

    def setUp(self):
        self.runner = _load_runner()

    def _make_context(self):
        return self.runner.SpecContext(
            title="Teste de Conformidade",
            slug="teste-de-conformidade",
            source_path=Path("input.md"),
            source_text="Demanda de teste para validar seções obrigatórias.",
        )

    def test_render_complete_spec_has_all_21_sections(self):
        ctx = self._make_context()
        spec = self.runner.render_complete_spec(ctx)
        for section in REQUIRED_SECTIONS:
            self.assertIn(f"## {section}", spec, f"Seção ausente: {section}")

    def test_render_complete_spec_has_handoff(self):
        ctx = self._make_context()
        spec = self.runner.render_complete_spec(ctx)
        self.assertIn("## Handoff Para Desenvolvimento", spec)

    def test_render_documents_returns_7_artifacts(self):
        ctx = self._make_context()
        docs = self.runner.render_documents(ctx)
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


if __name__ == "__main__":
    unittest.main()
