from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AGENT_DIR = ROOT / "agents" / "presentation-deck-builder"
CAPABILITIES_DIR = AGENT_DIR / "capabilities"
CATALOG = AGENT_DIR / "knowledge" / "template-catalog.yaml"
CLI = ROOT / "ai-devkit"

SMOKE_COVERAGE = {
    "create-template-version",
    "deprecate-template-version",
    "generate-deck-from-template",
    "generate-template-input-file",
    "list-template-versions",
    "list-templates",
    "promote-template-version",
    "refine-template",
    "register-template",
}


class PresentationDeckBuilderRunnerSmokeTest(unittest.TestCase):
    maxDiff = None

    def test_all_runner_capabilities_have_smoke_coverage(self) -> None:
        discovered = {
            path.parent.name for path in CAPABILITIES_DIR.glob("*/runner.py")
        }

        self.assertEqual(discovered, SMOKE_COVERAGE)

    def test_template_management_runners_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            templates_root = tmp / "templates"

            self._register_template(
                tmp,
                templates_root,
                template_id="runner-smoke",
                version="1.0.0",
                status="draft",
            )

            self._assert_ok(
                self._run("list-templates", "--templates-root", str(templates_root))
            )
            self._assert_ok(
                self._run(
                    "list-template-versions",
                    "--template-id",
                    "runner-smoke",
                    "--templates-root",
                    str(templates_root),
                )
            )
            self._assert_ok(
                self._run(
                    "generate-template-input-file",
                    "--template-id",
                    "runner-smoke",
                    "--template-version",
                    "1.0.0",
                    "--templates-root",
                    str(templates_root),
                )
            )
            self._assert_ok(
                self._run(
                    "promote-template-version",
                    "--template-id",
                    "runner-smoke",
                    "--template-version",
                    "1.0.0",
                    "--templates-root",
                    str(templates_root),
                    "--yes-confirm",
                    "--confirm-execute",
                )
            )
            self._assert_ok(
                self._run(
                    "create-template-version",
                    "--template-id",
                    "runner-smoke",
                    "--base-version",
                    "1.0.0",
                    "--new-version",
                    "1.1.0",
                    "--templates-root",
                    str(templates_root),
                )
            )
            self._assert_ok(
                self._run(
                    "refine-template",
                    "--template-id",
                    "runner-smoke",
                    "--base-version",
                    "1.1.0",
                    "--new-version",
                    "1.1.1",
                    "--change-request",
                    "Ajustar capa executiva para o smoke test.",
                    "--templates-root",
                    str(templates_root),
                )
            )
            self._assert_ok(
                self._run(
                    "deprecate-template-version",
                    "--template-id",
                    "runner-smoke",
                    "--template-version",
                    "1.1.1",
                    "--reason",
                    "Versao temporaria do smoke test.",
                    "--templates-root",
                    str(templates_root),
                    "--yes-confirm",
                    "--confirm-execute",
                )
            )

    @unittest.skipUnless(
        (
            Path.home()
            / ".codex"
            / "plugins"
            / "cache"
            / "openai-primary-runtime"
            / "presentations"
        ).exists()
        or os.environ.get("PRESENTATIONS_SKILL_DIR"),
        "presentations skill (@oai/artifact-tool) not available in this environment",
    )
    def test_generate_deck_runner_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            templates_root = tmp / "templates"
            input_path = tmp / "deck-input.json"
            output_path = tmp / "deck.pptx"

            self._register_template(
                tmp,
                templates_root,
                template_id="deck-smoke",
                version="1.0.0",
                status="validated",
            )
            input_path.write_text(
                json.dumps(
                    {
                        "title": "Smoke Test",
                        "subtitle": "Presentation deck builder",
                        "metrics": [
                            {"label": "Templates", "value": "1"},
                            {"label": "Runners", "value": "9"},
                        ],
                        "state_breakdown": {"ok": 1},
                        "highlights": ["Teste local sem servico externo."],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = self._run(
                "generate-deck-from-template",
                "--template-id",
                "deck-smoke",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--templates-root",
                str(templates_root),
            )

            self._assert_ok(result)
            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 0)
            self.assertEqual(output_path.read_bytes()[:2], b"PK")

    def _register_template(
        self,
        tmp: Path,
        templates_root: Path,
        *,
        template_id: str,
        version: str,
        status: str,
    ) -> None:
        template_path = tmp / f"{template_id}.pptx"
        template_path.write_bytes(b"fake pptx content")

        original_catalog = CATALOG.read_text(encoding="utf-8") if CATALOG.exists() else None
        try:
            result = self._run(
                "register-template",
                "--template",
                str(template_path),
                "--template-id",
                template_id,
                "--name",
                template_id.replace("-", " ").title(),
                "--version",
                version,
                "--status",
                status,
                "--templates-root",
                str(templates_root),
                "--yes-save",
                "--confirm-execute",
            )
            self._assert_ok(result)
        finally:
            if original_catalog is None:
                CATALOG.unlink(missing_ok=True)
            else:
                CATALOG.write_text(original_catalog, encoding="utf-8")

    def _run(self, capability: str, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.setdefault("AI_DEVKIT_RUN_TIMEOUT", "120")
        return subprocess.run(
            [
                sys.executable,
                str(CLI),
                "run",
                "presentation-deck-builder",
                capability,
                *args,
            ],
            cwd=ROOT,
            env=env,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _assert_ok(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.strip(), result.stderr)


if __name__ == "__main__":
    unittest.main()
