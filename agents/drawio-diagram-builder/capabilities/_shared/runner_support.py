#!/usr/bin/env python3
"""Shared runner support for Draw.io Diagram Builder."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
ROOT = AGENT_DIR.parents[1]
DRAWIO_DIR = AGENT_DIR / "infra" / "integrations" / "drawio"

sys.path.insert(0, str(DRAWIO_DIR))

from drawio_renderer import load_spec, render_drawio, write_json  # pylint: disable=import-error
from spec_builder import apply_feedback_to_spec, build_specialized_spec  # pylint: disable=import-error
from source_reader import load_sources  # pylint: disable=import-error
from validators import render_review, validate_drawio  # pylint: disable=import-error


def add_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--text")
    parser.add_argument("--brief")
    parser.add_argument("--file", action="append", dest="files")
    parser.add_argument("--directory")
    parser.add_argument("--url")


def add_generation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--diagram-type")
    parser.add_argument("--title")
    parser.add_argument("--audience")
    parser.add_argument("--detail-level")


def write_text(path: str | Path, content: str, yes_overwrite: bool = False) -> None:
    target = Path(path)
    if target.exists() and not yes_overwrite:
        raise ValueError(f"arquivo ja existe, use --yes-overwrite para sobrescrever: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def write_output(content: str, output: str | None) -> None:
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(content, encoding="utf-8")
    else:
        print(content)


def print_error(exc: Exception) -> int:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1


def run_interview() -> int:
    parser = argparse.ArgumentParser(description="Run drawio-diagram-builder/conduct-diagram-interview")
    parser.add_argument("--brief")
    parser.add_argument("--diagram-type")
    parser.add_argument("--audience")
    parser.add_argument("--detail-level")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        questions = build_interview(args)
        write_output(questions, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def build_interview(args: argparse.Namespace) -> str:
    missing = []
    if not args.brief:
        missing.append("objetivo e contexto do diagrama")
    if not args.diagram_type:
        missing.append("tipo de diagrama desejado")
    if not args.audience:
        missing.append("audiencia principal")
    if not args.detail_level:
        missing.append("nivel de detalhe")

    lines = [
        "# Diagram Interview",
        "",
        "## Perguntas",
        "",
    ]
    if missing:
        lines.append(f"- Para avancar, preciso esclarecer: {', '.join(missing)}.")
    lines.extend(
        [
            "- Qual decisao ou entendimento o diagrama precisa viabilizar?",
            "- Quem vai consumir o diagrama: negocio, produto, engenharia, operacao ou cliente?",
            "- O diagrama deve mostrar visao executiva, operacional ou tecnica detalhada?",
            "- Quais sistemas, atores, etapas ou regras nao podem faltar?",
            "- O que deve ficar fora do escopo para evitar poluicao visual?",
            "- Existem documentos, pastas, cards Azure ou specs que devem ser usados como fonte?",
            "- A entrega esperada e um unico diagrama ou um pacote com multiplas visoes?",
        ]
    )
    return "\n".join(lines) + "\n"


def run_ingest() -> int:
    parser = argparse.ArgumentParser(description="Run drawio-diagram-builder/ingest-diagram-sources")
    add_source_args(parser)
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = load_sources(text=args.text or args.brief, files=args.files, directory=args.directory, url=args.url)
        if args.output:
            write_json(args.output, payload)
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
    except Exception as exc:
        return print_error(exc)
    return 0


def run_read_azure_card() -> int:
    parser = argparse.ArgumentParser(description="Run drawio-diagram-builder/read-azure-card-context")
    parser.add_argument("--id", type=int, required=True)
    parser.add_argument("--project")
    parser.add_argument("--include-comments", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        command = [
            sys.executable,
            str(ROOT / "ai-devkit"),
            "run",
            "azure-devops-orchestrator",
            "read-card",
            "--id",
            str(args.id),
        ]
        if args.project:
            command.extend(["--project", args.project])
        if args.include_comments:
            command.append("--include-comments")
        result = subprocess.run(command, cwd=ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise ValueError(result.stderr.strip() or "azure card read failed")
        write_output(result.stdout, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def run_analyze() -> int:
    parser = argparse.ArgumentParser(description="Run drawio-diagram-builder/analyze-diagram-context")
    add_source_args(parser)
    add_generation_args(parser)
    parser.add_argument("--source-context")
    parser.add_argument("--spec-output")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        context = load_context_or_sources(args)
        spec = build_specialized_spec(
            context.get("combined_text", ""),
            diagram_type=args.diagram_type,
            title=args.title,
            audience=args.audience,
            detail_level=args.detail_level,
        )
        if args.spec_output:
            write_json(args.spec_output, spec)
        write_output(render_plan(spec, context), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def run_plan() -> int:
    parser = argparse.ArgumentParser(description="Run drawio-diagram-builder/plan-diagram")
    parser.add_argument("--brief")
    parser.add_argument("--source-context")
    parser.add_argument("--diagram-type")
    parser.add_argument("--title")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        if args.source_context:
            context = json.loads(Path(args.source_context).read_text(encoding="utf-8"))
            text = context.get("combined_text", "")
        else:
            context = {"source_count": 1 if args.brief else 0}
            text = args.brief or ""
        spec = build_specialized_spec(text, diagram_type=args.diagram_type, title=args.title)
        write_output(render_plan(spec, context), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def run_generate(forced_type: str | None = None, default_output: str = "diagram.drawio") -> int:
    parser = argparse.ArgumentParser(description="Run drawio-diagram-builder/generate-drawio-diagram")
    parser.add_argument("--spec")
    add_source_args(parser)
    add_generation_args(parser)
    parser.add_argument("--output", default=default_output)
    parser.add_argument("--spec-output")
    parser.add_argument("--notes-output")
    parser.add_argument("--yes-overwrite", action="store_true")
    args = parser.parse_args()
    try:
        spec = resolve_spec(args, forced_type=forced_type)
        xml = render_drawio(spec)
        write_text(args.output, xml, yes_overwrite=args.yes_overwrite)
        if args.spec_output:
            write_json(args.spec_output, spec)
        if args.notes_output:
            write_text(args.notes_output, render_notes(spec), yes_overwrite=args.yes_overwrite)
        print(f"Diagrama gerado: {args.output}")
    except Exception as exc:
        return print_error(exc)
    return 0


def run_generate_architecture() -> int:
    return run_generate(forced_type="architecture", default_output="architecture.drawio")


def run_generate_flow() -> int:
    return run_generate(forced_type="flowchart", default_output="flow.drawio")


def run_generate_erd() -> int:
    return run_generate(forced_type="erd", default_output="erd.drawio")


def run_review() -> int:
    parser = argparse.ArgumentParser(description="Run drawio-diagram-builder/review-drawio-diagram")
    parser.add_argument("--diagram", required=True)
    parser.add_argument("--spec")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        review = render_review(validate_drawio(args.diagram))
        write_output(review, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def run_refine() -> int:
    parser = argparse.ArgumentParser(description="Run drawio-diagram-builder/refine-drawio-diagram")
    parser.add_argument("--diagram", required=True)
    parser.add_argument("--spec")
    parser.add_argument("--feedback", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--spec-output")
    parser.add_argument("--changelog-output")
    parser.add_argument("--yes-overwrite", action="store_true")
    args = parser.parse_args()
    try:
        spec = load_spec(args.spec) if args.spec else spec_from_existing_diagram(args.diagram)
        refined_spec, changes = apply_feedback_to_spec(spec, args.feedback)
        write_text(args.output, render_drawio(refined_spec), yes_overwrite=args.yes_overwrite)
        if args.spec_output:
            write_json(args.spec_output, refined_spec)
        changelog = "# Diagram Changelog\n\n" + "\n".join(f"- {change}" for change in changes) + "\n"
        if args.changelog_output:
            write_text(args.changelog_output, changelog, yes_overwrite=args.yes_overwrite)
        print(f"Diagrama refinado: {args.output}")
    except Exception as exc:
        return print_error(exc)
    return 0


def run_execute_delivery() -> int:
    parser = argparse.ArgumentParser(description="Run drawio-diagram-builder/execute-diagram-delivery")
    add_source_args(parser)
    parser.add_argument("--azure-project")
    parser.add_argument("--azure-card", type=int)
    add_generation_args(parser)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--yes-create-dir", action="store_true")
    parser.add_argument("--yes-overwrite", action="store_true")
    args = parser.parse_args()
    try:
        output_dir = Path(args.output_dir)
        if output_dir.exists() is False and not args.yes_create_dir:
            raise ValueError(f"diretorio nao existe, use --yes-create-dir para criar: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

        extra_text = args.text or args.brief or ""
        if args.azure_card:
            extra_text = (extra_text + "\n\n" + read_azure_card_text(args.azure_card, args.azure_project)).strip()
        context = load_sources(text=extra_text or None, files=args.files, directory=args.directory, url=args.url)
        spec = build_specialized_spec(
            context.get("combined_text", ""),
            diagram_type=args.diagram_type,
            title=args.title,
            audience=args.audience,
            detail_level=args.detail_level,
        )
        delivery_status = "needs_answers" if spec.get("open_questions") else "ready"
        write_text(output_dir / "diagram-interview.md", render_interview_from_spec(spec), yes_overwrite=args.yes_overwrite)
        write_json(
            output_dir / "delivery-status.json",
            {
                "delivery_status": delivery_status,
                "open_question_count": len(spec.get("open_questions") or []),
            },
        )
        write_json(output_dir / "source-context.json", context)
        write_json(output_dir / "diagram-spec.json", spec)
        write_text(output_dir / "diagram-plan.md", render_plan(spec, context), yes_overwrite=args.yes_overwrite)
        write_text(output_dir / "open-questions.md", render_open_questions(spec), yes_overwrite=args.yes_overwrite)
        write_text(output_dir / "diagram.drawio", render_drawio(spec), yes_overwrite=args.yes_overwrite)
        write_text(output_dir / "diagram-review.md", render_review(validate_drawio(output_dir / "diagram.drawio")), yes_overwrite=args.yes_overwrite)
        print(f"Pacote de diagrama gerado: {output_dir}")
    except Exception as exc:
        return print_error(exc)
    return 0


def load_context_or_sources(args: argparse.Namespace) -> dict[str, Any]:
    if getattr(args, "source_context", None):
        return json.loads(Path(args.source_context).read_text(encoding="utf-8"))
    return load_sources(text=args.text or args.brief, files=args.files, directory=args.directory, url=args.url)


def resolve_spec(args: argparse.Namespace, forced_type: str | None = None) -> dict[str, Any]:
    if args.spec:
        spec = load_spec(args.spec)
        if forced_type:
            spec["diagram_type"] = forced_type
        return spec
    context = load_context_or_sources(args)
    return build_specialized_spec(
        context.get("combined_text", ""),
        diagram_type=forced_type or args.diagram_type,
        title=args.title,
        audience=args.audience,
        detail_level=args.detail_level,
    )


def spec_from_existing_diagram(diagram: str) -> dict[str, Any]:
    return {
        "title": Path(diagram).stem,
        "diagram_type": "flowchart",
        "nodes": [],
        "edges": [],
        "open_questions": ["Spec original nao foi informada para refinamento semantico."],
    }


def read_azure_card_text(card_id: int, project: str | None) -> str:
    command = [
        sys.executable,
        str(ROOT / "ai-devkit"),
        "run",
        "azure-devops-orchestrator",
        "read-card",
        "--id",
        str(card_id),
        "--include-comments",
    ]
    if project:
        command.extend(["--project", project])
    result = subprocess.run(command, cwd=ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or "azure card read failed")
    return result.stdout


def render_plan(spec: dict[str, Any], context: dict[str, Any]) -> str:
    lines = [
        "# Diagram Plan",
        "",
        f"- Titulo: {spec.get('title')}",
        f"- Tipo: {spec.get('diagram_type')}",
        f"- Audiencia: {spec.get('audience', '-')}",
        f"- Nivel de detalhe: {spec.get('detail_level', '-')}",
        f"- Fontes analisadas: {context.get('source_count', 0)}",
        f"- Nos previstos: {len(spec.get('nodes') or [])}",
        f"- Conectores previstos: {len(spec.get('edges') or [])}",
        "",
        "## Fatos",
        "",
    ]
    facts = spec.get("facts") or []
    lines.extend(f"- {fact}" for fact in facts) if facts else lines.append("- Nenhum fato extraido.")
    lines.extend(["", "## Premissas", ""])
    assumptions = spec.get("assumptions") or []
    lines.extend(f"- {item}" for item in assumptions) if assumptions else lines.append("- Nenhuma premissa registrada.")
    lines.extend(["", "## Perguntas Abertas", ""])
    questions = spec.get("open_questions") or []
    lines.extend(f"- {item}" for item in questions) if questions else lines.append("- Nenhuma pergunta aberta.")
    return "\n".join(lines) + "\n"


def render_open_questions(spec: dict[str, Any]) -> str:
    questions = spec.get("open_questions") or []
    lines = ["# Open Questions", ""]
    lines.extend(f"- {question}" for question in questions) if questions else lines.append("- Nenhuma pergunta aberta.")
    return "\n".join(lines) + "\n"


def render_interview_from_spec(spec: dict[str, Any]) -> str:
    lines = [
        "# Diagram Interview",
        "",
        "## Perguntas Abertas",
        "",
    ]
    questions = spec.get("open_questions") or []
    lines.extend(f"- {question}" for question in questions) if questions else lines.append("- Nenhuma pergunta aberta.")
    lines.extend(
        [
            "",
            "## Confirmacoes",
            "",
            f"- Titulo proposto: {spec.get('title')}",
            f"- Tipo proposto: {spec.get('diagram_type')}",
            f"- Audiencia proposta: {spec.get('audience', '-')}",
        ]
    )
    return "\n".join(lines) + "\n"


def render_notes(spec: dict[str, Any]) -> str:
    return (
        "# Diagram Notes\n\n"
        f"- Titulo: {spec.get('title')}\n"
        f"- Tipo: {spec.get('diagram_type')}\n"
        f"- Nos: {len(spec.get('nodes') or [])}\n"
        f"- Conectores: {len(spec.get('edges') or [])}\n"
    )
