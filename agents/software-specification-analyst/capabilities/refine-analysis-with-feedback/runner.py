#!/usr/bin/env python3
"""Runner for software-specification-analyst/refine-analysis-with-feedback."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import unicodedata


DOCUMENTS = {
    "refined-analysis.md": "render_refined_analysis",
    "resolved-questions.md": "render_resolved_questions",
    "remaining-open-questions.md": "render_remaining_questions",
    "decision-log.md": "render_decision_log",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run software-specification-analyst/refine-analysis-with-feedback"
    )
    parser.add_argument("--analysis-dir", required=True)
    parser.add_argument("--feedback", required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--strictness", choices=["normal", "strict"], default="normal")
    parser.add_argument("--yes-create-dir", action="store_true")
    parser.add_argument("--yes-overwrite", action="store_true")
    args = parser.parse_args()

    try:
        analysis_dir = Path(args.analysis_dir).expanduser().resolve()
        feedback_path = Path(args.feedback).expanduser().resolve()
        if not analysis_dir.exists() or not analysis_dir.is_dir():
            raise ValueError(f"analysis directory not found: {analysis_dir}")
        if not feedback_path.exists():
            raise ValueError(f"feedback not found: {feedback_path}")
        analysis = read_markdown_dir(analysis_dir)
        feedback = feedback_path.read_text(encoding="utf-8")
        title = infer_title(feedback, analysis, feedback_path)
        output_dir = resolve_output_dir(args.output_dir, f"{slugify(title)}-refined")
        ensure_output_dir(output_dir, args.yes_create_dir)
        documents = render_documents(title, analysis, feedback, args.strictness)
        write_documents(output_dir, documents, args.yes_overwrite)
        print_summary(output_dir, documents)
    except KeyboardInterrupt:
        print("\nOperacao cancelada.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def render_documents(title: str, analysis: str, feedback: str, strictness: str) -> dict[str, str]:
    questions = extract_questions(analysis)
    decisions = extract_decisions(feedback)
    context = {
        "title": title,
        "analysis": analysis.strip(),
        "feedback": feedback.strip(),
        "strictness": strictness,
        "questions": questions,
        "decisions": decisions,
    }
    renderers = {
        "render_refined_analysis": render_refined_analysis,
        "render_resolved_questions": render_resolved_questions,
        "render_remaining_questions": render_remaining_questions,
        "render_decision_log": render_decision_log,
    }
    return {name: renderers[renderer](context) for name, renderer in DOCUMENTS.items()}


def render_refined_analysis(context: dict) -> str:
    return f"""# Analise Refinada: {context['title']}

## Feedback Incorporado

{quote(context['feedback'])}

## Fatos Confirmados Pelo Feedback

{render_bullets(context['decisions'])}

## Analise Original Consolidada

{quote(context['analysis'][:12000])}

## Status

- Strictness: `{context['strictness']}`
- Esta analise pode alimentar `create-final-spec-from-analysis`.
"""


def render_resolved_questions(context: dict) -> str:
    return f"""# Perguntas Resolvidas: {context['title']}

## Respostas Incorporadas

{render_bullets(context['decisions'])}

## Perguntas Originais Consideradas

{render_bullets(context['questions'][:20])}
"""


def render_remaining_questions(context: dict) -> str:
    return f"""# Perguntas Ainda Abertas: {context['title']}

- Validar excecoes e fluxos alternativos nao respondidos.
- Confirmar dados obrigatorios, dados sensiveis e auditoria.
- Confirmar integracoes externas e contratos tecnicos.
- Confirmar criterio mensuravel de sucesso.
"""


def render_decision_log(context: dict) -> str:
    rows = []
    for index, decision in enumerate(context["decisions"][:20], start=1):
        rows.append(f"| DEC-{index:03d} | {decision} | Feedback | Confirmado pelo usuario |")
    if not rows:
        rows.append("| DEC-001 | Nenhuma decisao explicita identificada | Feedback | Pendente |")
    return "# Registro De Decisoes\n\n| ID | Decisao | Fonte | Status |\n|---|---|---|---|\n" + "\n".join(rows) + "\n"


def read_markdown_dir(directory: Path) -> str:
    chunks = []
    for file in sorted(directory.glob("*.md")):
        chunks.append(f"# Fonte: {file.name}\n\n{file.read_text(encoding='utf-8')}")
    return "\n\n".join(chunks)


def extract_questions(text: str) -> list[str]:
    return [line.strip().lstrip("- ").strip() for line in text.splitlines() if line.strip().endswith("?")]


def extract_decisions(text: str) -> list[str]:
    decisions = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("- ").strip()
        if stripped and not stripped.startswith("#"):
            decisions.append(stripped)
    return decisions


def infer_title(feedback: str, analysis: str, fallback: Path) -> str:
    generic = {"respostas", "feedback", "analise", "contexto", "perguntas"}
    for text in (feedback, analysis):
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                title = stripped.lstrip("#").strip()
                if title and title.lower() not in generic and not title.lower().startswith("fonte:"):
                    return title
    return fallback.stem.replace("-", " ").replace("_", " ").title()


def normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return re.sub(r"[^a-zA-Z0-9]+", "", normalized.encode("ascii", "ignore").decode("ascii")).lower()


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", normalize(value)).strip("-") or "refined-analysis"


def resolve_output_dir(output_dir: str | None, slug: str) -> Path:
    return Path(output_dir).expanduser().resolve() if output_dir else Path.cwd() / "specifications" / slug


def ensure_output_dir(output_dir: Path, yes_create_dir: bool) -> None:
    if output_dir.exists():
        if not output_dir.is_dir():
            raise ValueError(f"output path exists and is not a directory: {output_dir}")
        return
    if not yes_create_dir:
        answer = input(f"Criar pasta de analise refinada em {output_dir}? [s/N] ").strip().lower()
        if answer not in {"s", "sim", "y", "yes"}:
            raise ValueError("criacao da pasta nao autorizada")
    output_dir.mkdir(parents=True, exist_ok=False)


def write_documents(output_dir: Path, documents: dict[str, str], yes_overwrite: bool) -> None:
    existing = [name for name in documents if (output_dir / name).exists()]
    if existing and not yes_overwrite:
        answer = input("Sobrescrever arquivos existentes? [s/N] ").strip().lower()
        if answer not in {"s", "sim", "y", "yes"}:
            raise ValueError("sobrescrita nao autorizada")
    for name, content in documents.items():
        (output_dir / name).write_text(content.rstrip() + "\n", encoding="utf-8")


def print_summary(output_dir: Path, documents: dict[str, str]) -> None:
    print("# Software Specification Analyst")
    print("")
    print(f"Documentos de analise refinada gerados em: {output_dir}")
    print("")
    for name in documents:
        print(f"- {output_dir / name}")


def quote(text: str) -> str:
    return "\n".join(f"> {line}" if line else ">" for line in text.splitlines()) or "> Nenhum conteudo."


def render_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- Nenhum item identificado."


if __name__ == "__main__":
    raise SystemExit(main())
