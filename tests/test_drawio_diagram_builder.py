#!/usr/bin/env python3
"""Tests for drawio-diagram-builder."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "ai-devkit"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class DrawioDiagramBuilderTest(unittest.TestCase):
    def test_cli_lists_drawio_agent_and_capabilities(self) -> None:
        agents = run_cli("--json", "agents")
        self.assertEqual(agents.returncode, 0, agents.stderr)
        payload = json.loads(agents.stdout)
        self.assertIn("drawio-diagram-builder", {item["id"] for item in payload["items"]})

        capabilities = run_cli("--json", "capabilities", "drawio-diagram-builder")
        self.assertEqual(capabilities.returncode, 0, capabilities.stderr)
        names = {item["id"].split(".")[-1] for item in json.loads(capabilities.stdout)["items"]}
        self.assertGreaterEqual(
            names,
            {
                "conduct-diagram-interview",
                "ingest-diagram-sources",
                "analyze-diagram-context",
                "generate-drawio-diagram",
                "review-drawio-diagram",
                "refine-drawio-diagram",
                "execute-diagram-delivery",
            },
        )

    def test_generate_drawio_diagram_creates_valid_mxfile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec = Path(tmpdir) / "diagram-spec.json"
            output = Path(tmpdir) / "journey.drawio"
            spec.write_text(
                json.dumps(
                    {
                        "title": "Jornada de Onboarding",
                        "diagram_type": "user_journey",
                        "nodes": [
                            {"id": "start", "label": "Cliente inicia cadastro", "group": "Cliente"},
                            {"id": "api", "label": "API valida dados", "group": "Sistema"},
                            {"id": "done", "label": "Conta liberada", "group": "Sistema"},
                        ],
                        "edges": [
                            {"source": "start", "target": "api", "label": "envia dados"},
                            {"source": "api", "target": "done", "label": "aprovado"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = run_cli(
                "run",
                "drawio-diagram-builder",
                "generate-drawio-diagram",
                "--spec",
                str(spec),
                "--output",
                str(output),
                "--yes-overwrite",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.exists())
            root = ElementTree.fromstring(output.read_text(encoding="utf-8"))
            self.assertEqual(root.tag, "mxfile")
            xml_text = output.read_text(encoding="utf-8")
            self.assertIn("Jornada de Onboarding", xml_text)
            self.assertIn("Cliente inicia cadastro", xml_text)
            self.assertIn("source=\"node-start\"", xml_text)

    def test_ingest_sources_reads_common_local_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "sources"
            output = Path(tmpdir) / "source-context.json"
            source_dir.mkdir()
            (source_dir / "brief.md").write_text("# Fluxo\nCliente solicita limite.", encoding="utf-8")
            (source_dir / "contract.json").write_text(
                json.dumps({"endpoint": "/customers/{id}/limit"}), encoding="utf-8"
            )
            xlsx = source_dir / "rules.xlsx"
            with zipfile.ZipFile(xlsx, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(
                    "xl/worksheets/sheet1.xml",
                    '<worksheet><sheetData><row><c t="inlineStr"><is><t>Regra de limite</t></is></c></row></sheetData></worksheet>',
                )

            result = run_cli(
                "run",
                "drawio-diagram-builder",
                "ingest-diagram-sources",
                "--directory",
                str(source_dir),
                "--output",
                str(output),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["source_count"], 3)
            combined = "\n".join(item["text"] for item in payload["sources"])
            self.assertIn("Cliente solicita limite", combined)
            self.assertIn("/customers/{id}/limit", combined)
            self.assertIn("Regra de limite", combined)

    def test_ingest_sources_records_failed_files_without_losing_valid_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            good = Path(tmpdir) / "brief.md"
            missing = Path(tmpdir) / "missing.md"
            output = Path(tmpdir) / "source-context.json"
            good.write_text("Cliente acessa portal.", encoding="utf-8")

            result = run_cli(
                "run",
                "drawio-diagram-builder",
                "ingest-diagram-sources",
                "--file",
                str(good),
                "--file",
                str(missing),
                "--output",
                str(output),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["source_count"], 1)
            self.assertEqual(len(payload["failed_sources"]), 1)
            self.assertIn("missing.md", payload["failed_sources"][0]["path"])

    def test_execute_diagram_delivery_generates_reviewed_drawio(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "spec.md"
            output_dir = Path(tmpdir) / "out"
            source.write_text(
                "# Checkout\nUsuario escolhe produto. Sistema calcula frete. Pagamento confirma pedido.",
                encoding="utf-8",
            )

            result = run_cli(
                "run",
                "drawio-diagram-builder",
                "execute-diagram-delivery",
                "--file",
                str(source),
                "--diagram-type",
                "flowchart",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output_dir / "diagram.drawio").exists())
            self.assertTrue((output_dir / "diagram-review.md").exists())
            review = (output_dir / "diagram-review.md").read_text(encoding="utf-8")
            self.assertIn("XML valido", review)

    def test_generate_erd_diagram_extracts_entities_and_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "erd.drawio"
            spec_output = Path(tmpdir) / "erd-spec.json"

            result = run_cli(
                "run",
                "drawio-diagram-builder",
                "generate-erd-diagram",
                "--brief",
                "Tabela cliente possui id nome cpf. Tabela pedido possui id cliente_id valor. Pedido pertence a cliente.",
                "--output",
                str(output),
                "--spec-output",
                str(spec_output),
                "--yes-overwrite",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            spec = json.loads(spec_output.read_text(encoding="utf-8"))
            labels = {node["label"] for node in spec["nodes"]}
            self.assertIn("cliente", labels)
            self.assertIn("pedido", labels)
            pedido = next(node for node in spec["nodes"] if node["id"] == "pedido")
            self.assertIn("cliente_id", pedido["attributes"])
            self.assertTrue(all(node["kind"] == "entity" for node in spec["nodes"]))
            self.assertIn(
                ("pedido", "cliente"),
                {(edge["source"], edge["target"]) for edge in spec["edges"]},
            )
            self.assertIn("cliente_id", output.read_text(encoding="utf-8"))
            self.assertIn("nome", output.read_text(encoding="utf-8"))

    def test_generate_architecture_diagram_extracts_architecture_groups(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_output = Path(tmpdir) / "arch-spec.json"

            result = run_cli(
                "run",
                "drawio-diagram-builder",
                "generate-architecture-diagram",
                "--brief",
                "Cliente acessa app mobile. App mobile chama API Gateway. API Gateway chama servico de cadastro. Servico de cadastro grava no banco Postgres.",
                "--output",
                str(Path(tmpdir) / "arch.drawio"),
                "--spec-output",
                str(spec_output),
                "--yes-overwrite",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            spec = json.loads(spec_output.read_text(encoding="utf-8"))
            groups = {node["group"] for node in spec["nodes"]}
            self.assertGreaterEqual(groups, {"Atores", "Canais", "Servicos", "Dados"})
            self.assertIn("banco Postgres", {node["label"] for node in spec["nodes"]})
            edge_labels = {edge["label"] for edge in spec["edges"]}
            self.assertIn("acessa", edge_labels)
            self.assertIn("chama", edge_labels)
            self.assertIn("grava", edge_labels)

    def test_generate_flow_diagram_extracts_decision_node(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_output = Path(tmpdir) / "flow-spec.json"

            result = run_cli(
                "run",
                "drawio-diagram-builder",
                "generate-flow-diagram",
                "--brief",
                "Usuario envia pedido. Sistema valida estoque. Se pagamento aprovado, sistema confirma pedido. Caso contrario, sistema solicita outro metodo.",
                "--output",
                str(Path(tmpdir) / "flow.drawio"),
                "--spec-output",
                str(spec_output),
                "--yes-overwrite",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            spec = json.loads(spec_output.read_text(encoding="utf-8"))
            self.assertIn("decision", {node["kind"] for node in spec["nodes"]})

    def test_refine_drawio_diagram_updates_spec_and_rerenders(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "diagram-spec.json"
            diagram_path = Path(tmpdir) / "diagram.drawio"
            refined_path = Path(tmpdir) / "diagram-refined.drawio"
            refined_spec_path = Path(tmpdir) / "diagram-spec-refined.json"
            spec_path.write_text(
                json.dumps(
                    {
                        "title": "Arquitetura",
                        "diagram_type": "architecture",
                        "nodes": [{"id": "api", "label": "API", "group": "Servicos", "kind": "system"}],
                        "edges": [],
                    }
                ),
                encoding="utf-8",
            )
            generate = run_cli(
                "run",
                "drawio-diagram-builder",
                "generate-drawio-diagram",
                "--spec",
                str(spec_path),
                "--output",
                str(diagram_path),
                "--yes-overwrite",
            )
            self.assertEqual(generate.returncode, 0, generate.stderr)

            result = run_cli(
                "run",
                "drawio-diagram-builder",
                "refine-drawio-diagram",
                "--diagram",
                str(diagram_path),
                "--spec",
                str(spec_path),
                "--feedback",
                "renomeie API para API Gateway",
                "--output",
                str(refined_path),
                "--spec-output",
                str(refined_spec_path),
                "--yes-overwrite",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            refined_spec = json.loads(refined_spec_path.read_text(encoding="utf-8"))
            self.assertEqual(refined_spec["nodes"][0]["label"], "API Gateway")
            self.assertIn("API Gateway", refined_path.read_text(encoding="utf-8"))

    def test_execute_diagram_delivery_records_interview_when_context_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = run_cli(
                "run",
                "drawio-diagram-builder",
                "execute-diagram-delivery",
                "--brief",
                "Sistema valida pedido.",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output_dir / "diagram-interview.md").exists())
            status = json.loads((output_dir / "delivery-status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["delivery_status"], "needs_answers")

    def test_review_drawio_diagram_warns_about_overlapping_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            diagram = Path(tmpdir) / "overlap.drawio"
            diagram.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<mxfile><diagram id="d1" name="Overlap"><mxGraphModel><root>
<mxCell id="0"/><mxCell id="1" parent="0"/>
<mxCell id="diagram-title" value="Overlap" vertex="1" parent="1"><mxGeometry x="0" y="0" width="100" height="30" as="geometry"/></mxCell>
<mxCell id="node-a" value="A" vertex="1" parent="1"><mxGeometry x="100" y="100" width="120" height="60" as="geometry"/></mxCell>
<mxCell id="node-b" value="B" vertex="1" parent="1"><mxGeometry x="100" y="100" width="120" height="60" as="geometry"/></mxCell>
</root></mxGraphModel></diagram></mxfile>""",
                encoding="utf-8",
            )

            result = run_cli(
                "run",
                "drawio-diagram-builder",
                "review-drawio-diagram",
                "--diagram",
                str(diagram),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("sobrepostos", result.stdout)


if __name__ == "__main__":
    unittest.main()
