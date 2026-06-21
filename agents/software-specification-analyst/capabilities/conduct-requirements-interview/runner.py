#!/usr/bin/env python3
"""Runner for software-specification-analyst/conduct-requirements-interview."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import unicodedata


DOCUMENTS = {
    "interview-guide.md": "render_interview_guide",
    "stakeholder-questions.md": "render_stakeholder_questions",
    "missing-decisions.md": "render_missing_decisions",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run software-specification-analyst/conduct-requirements-interview"
    )
    parser.add_argument("--input", required=True, help="demanda inicial em Markdown/texto")
    parser.add_argument("--analysis-dir", help="diretorio com documentos de analise")
    parser.add_argument("--output-dir", help="diretorio onde os artefatos serao salvos")
    parser.add_argument("--depth", choices=["light", "medium", "deep"], default="medium")
    parser.add_argument("--audience", help="publico da entrevista")
    parser.add_argument("--yes-create-dir", action="store_true")
    parser.add_argument("--yes-overwrite", action="store_true")
    args = parser.parse_args()

    try:
        input_path = Path(args.input).expanduser().resolve()
        if not input_path.exists():
            raise ValueError(f"input not found: {input_path}")
        demand = input_path.read_text(encoding="utf-8")
        analysis = read_markdown_dir(args.analysis_dir)
        title = infer_title(demand, input_path)
        output_dir = resolve_output_dir(args.output_dir, f"{slugify(title)}-interview")
        ensure_output_dir(output_dir, args.yes_create_dir)
        documents = render_documents(title, demand, analysis, args.depth, args.audience)
        write_documents(output_dir, documents, args.yes_overwrite)
        print_summary(output_dir, documents, "Documentos de entrevista gerados em")
    except KeyboardInterrupt:
        print("\nOperacao cancelada.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def render_documents(title: str, demand: str, analysis: str, depth: str, audience: str | None) -> dict[str, str]:
    renderers = {
        "render_interview_guide": render_interview_guide,
        "render_stakeholder_questions": render_stakeholder_questions,
        "render_missing_decisions": render_missing_decisions,
    }
    context = {
        "title": title,
        "demand": demand.strip(),
        "analysis": analysis.strip(),
        "depth": depth,
        "audience": audience or "stakeholders de negocio, produto, tecnologia e QA",
        "terms": extract_terms(f"{demand}\n{analysis}"),
        "questions": extract_questions(analysis),
    }
    return {name: renderers[renderer](context) for name, renderer in DOCUMENTS.items()}


def render_interview_guide(context: dict) -> str:
    return f"""# Roteiro De Entrevista: {context['title']}

## Profundidade

- Nivel: `{context['depth']}`
- Publico: {context['audience']}

## Objetivo Da Entrevista

Validar fatos, regras de negocio, excecoes, dados, permissoes e criterios de
sucesso antes da especificacao final.

## Contexto De Entrada

{quote(context['demand'])}

## Conceitos Para Validar

{render_terms(context['terms'])}

## Sequencia Recomendada

1. Confirmar problema e resultado esperado.
2. Confirmar atores e permissoes.
3. Validar regras e excecoes.
4. Validar dados, status e integracoes.
5. Fechar criterios de aceite e riscos.
"""


def render_stakeholder_questions(context: dict) -> str:
    inherited = "\n".join(f"- {question}" for question in context["questions"][:12])
    if not inherited:
        inherited = "- Nenhuma pergunta herdada da analise; usar perguntas abaixo."
    return f"""# Perguntas Para Stakeholders: {context['title']}

## Perguntas Herdadas Da Analise

{inherited}

## Negocio

- Qual problema de negocio esta demanda resolve?
- Qual resultado mensuravel indica sucesso?
- Quais regras atuais sao obrigatorias e quais podem mudar?

## Funcional

- Quem pode executar a jornada principal?
- Quais fluxos alternativos e excecoes precisam existir?
- Quais mensagens ou estados devem ser visiveis ao usuario?

## Dados E Permissoes

- Quais dados sao obrigatorios, sensiveis ou auditaveis?
- Quais papeis podem criar, alterar, consultar ou concluir o processo?

## QA

- Quais cenarios sao criticos para regressao?
- Quais dados de teste representam casos reais?
"""


def render_missing_decisions(context: dict) -> str:
    return f"""# Decisoes Pendentes: {context['title']}

| Decisao | Por Que Importa | Dono Sugerido |
|---|---|---|
| Atores e permissoes | Define acesso e auditoria | Produto/Seguranca |
| Regras de negocio obrigatorias | Evita especificar implementacao como regra | Negocio |
| Estados e transicoes | Determina jornadas e testes | Produto/QA |
| Dados obrigatorios e sensiveis | Impacta modelo, UI e compliance | Produto/Seguranca |
| Integracoes externas | Impacta arquitetura, rollback e testes | Engenharia |
"""


def read_markdown_dir(path: str | None) -> str:
    if not path:
        return ""
    directory = Path(path).expanduser().resolve()
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f"analysis directory not found: {directory}")
    chunks = []
    for file in sorted(directory.glob("*.md")):
        chunks.append(f"# Fonte: {file.name}\n\n{file.read_text(encoding='utf-8')}")
    return "\n\n".join(chunks)


def extract_questions(text: str) -> list[str]:
    questions = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("- ").strip()
        if stripped.endswith("?"):
            questions.append(stripped)
    return questions


def extract_terms(text: str) -> list[str]:
    terms: dict[str, int] = {}
    for raw in re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9_-]{4,}", text):
        term = normalize(raw)
        if term in {"contexto", "perguntas", "status", "fonte", "analysis"}:
            continue
        terms[term] = terms.get(term, 0) + 1
    return [term for term, _count in sorted(terms.items(), key=lambda item: (-item[1], item[0]))[:12]]


def infer_title(text: str, fallback: Path) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            if title:
                return title
    return fallback.stem.replace("-", " ").replace("_", " ").title()


def normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return re.sub(r"[^a-zA-Z0-9]+", "", normalized.encode("ascii", "ignore").decode("ascii")).lower()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalize(value)).strip("-")
    return slug or "requirements-interview"


def resolve_output_dir(output_dir: str | None, slug: str) -> Path:
    if output_dir:
        return Path(output_dir).expanduser().resolve()
    return Path.cwd() / "specifications" / slug


def ensure_output_dir(output_dir: Path, yes_create_dir: bool) -> None:
    if output_dir.exists():
        if not output_dir.is_dir():
            raise ValueError(f"output path exists and is not a directory: {output_dir}")
        return
    if not yes_create_dir:
        print("Posso criar a pasta de entrevista neste projeto?")
        print("")
        print("Caminho proposto:")
        print(str(output_dir))
        answer = input("Criar pasta? [s/N] ").strip().lower()
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


def print_summary(output_dir: Path, documents: dict[str, str], label: str) -> None:
    print("# Software Specification Analyst")
    print("")
    print(f"{label}: {output_dir}")
    print("")
    for name in documents:
        print(f"- {output_dir / name}")


def quote(text: str) -> str:
    return "\n".join(f"> {line}" if line else ">" for line in text.splitlines()) or "> Nenhum contexto fornecido."


def render_terms(terms: list[str]) -> str:
    if not terms:
        return "- Nenhum termo candidato identificado."
    return "\n".join(f"- {term}" for term in terms)


if __name__ == "__main__":
    raise SystemExit(main())
