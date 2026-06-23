#!/usr/bin/env python3
"""Runner for software-specification-analyst/create-final-spec-from-analysis."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import unicodedata


DOCUMENTS = {
    "software-specification.md": "render_software_spec",
    "functional-spec.md": "render_functional_spec",
    "technical-spec.md": "render_technical_spec",
    "user-stories.md": "render_user_stories",
    "journey-flows.md": "render_journey_flows",
    "requirements-traceability.md": "render_traceability",
    "open-questions.md": "render_open_questions",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run software-specification-analyst/create-final-spec-from-analysis"
    )
    parser.add_argument("--analysis-dir", required=True)
    parser.add_argument("--title")
    parser.add_argument("--output-dir")
    parser.add_argument("--include-technical-spec", action="store_true", default=True)
    parser.add_argument("--include-user-stories", action="store_true", default=True)
    parser.add_argument("--yes-create-dir", action="store_true")
    parser.add_argument("--yes-overwrite", action="store_true")
    args = parser.parse_args()

    try:
        analysis_dir = Path(args.analysis_dir).expanduser().resolve()
        if not analysis_dir.exists() or not analysis_dir.is_dir():
            raise ValueError(f"analysis directory not found: {analysis_dir}")
        analysis = read_markdown_dir(analysis_dir)
        title = args.title or infer_title(analysis, analysis_dir)
        output_dir = resolve_output_dir(args.output_dir, f"{slugify(title)}-final-spec")
        ensure_output_dir(output_dir, args.yes_create_dir)
        documents = render_documents(title, analysis)
        write_documents(output_dir, documents, args.yes_overwrite)
        print_summary(output_dir, documents)
    except KeyboardInterrupt:
        print("\nOperacao cancelada.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def render_documents(title: str, analysis: str) -> dict[str, str]:
    decisions = extract_decisions(analysis)
    questions = extract_questions(analysis)
    context = {"title": title, "analysis": analysis.strip(), "decisions": decisions, "questions": questions}
    renderers = {
        "render_software_spec": render_software_spec,
        "render_functional_spec": render_functional_spec,
        "render_technical_spec": render_technical_spec,
        "render_user_stories": render_user_stories,
        "render_journey_flows": render_journey_flows,
        "render_traceability": render_traceability,
        "render_open_questions": render_open_questions,
    }
    return {name: renderers[renderer](context) for name, renderer in DOCUMENTS.items()}


def render_software_spec(context: dict) -> str:
    return f"""# Especificacao De Software: {context['title']}

## Resumo Executivo

Esta especificacao foi gerada a partir de documentos de analise refinada,
feedback e decisoes registradas.

## Contexto E Problema

Pergunta Aberta: descrever o problema de negocio confirmado na analise.

## Objetivos

- Implementar a capacidade descrita e validada na analise.
- Preservar rastreabilidade entre decisoes, historias e criterios de aceite.

## Escopo

- Capacidade descrita e validada na analise.

## Fora De Escopo

- Implementacao de codigo.
- Efeitos colaterais em sistemas externos nao confirmados.

## Atores E Personas

Pergunta Aberta: confirmar atores e permissoes identificados na analise.

## Requisitos Funcionais

| ID | Requisito | Fonte |
|---|---|---|
| RF-001 | Permitir a jornada principal confirmada na analise. | Analise refinada |
| RF-002 | Aplicar regras, status e permissoes confirmadas. | Feedback |

## Requisitos Nao Funcionais

Pergunta Aberta: confirmar requisitos de seguranca, desempenho e disponibilidade.

## Regras De Negocio

## Decisoes Confirmadas

{render_bullets(context['decisions'])}

## User Stories

Consulte `user-stories.md`.

## Criterios De Aceite

Consulte `user-stories.md` — cada historia contem criterios de aceite.

## Jornadas E Fluxogramas

Consulte `journey-flows.md`.

## Modelo De Dados

Pergunta Aberta: confirmar entidades, atributos e classificacao de dados sensiveis.

## APIs E Integracoes

Pergunta Aberta: confirmar endpoints, eventos, jobs e sistemas externos.

## Permissoes E Seguranca

Pergunta Aberta: confirmar autenticacao, autorizacao, segregacao de papeis.

## Observabilidade

Pergunta Aberta: confirmar logs, metricas, traces, auditoria e alertas.

## Estrategia De Testes

- Unitarios: regras de negocio confirmadas.
- Integracao: contratos externos confirmados.
- E2E: jornada principal.
- Regressao: fluxos criticos.

## Riscos E Dependencias

Pergunta Aberta: revisar riscos identificados na analise.

## Matriz De Rastreabilidade

Consulte `requirements-traceability.md`.

## Perguntas Abertas

{render_bullets(context['questions'][:12])}

Consulte `open-questions.md` para lista completa.

## Handoff Para Desenvolvimento

Pacote de entrega: `functional-spec.md`, `technical-spec.md`,
`user-stories.md`, `journey-flows.md`, `requirements-traceability.md`,
`open-questions.md`.

Pendencias bloqueantes: resolver perguntas abertas classificadas como
bloqueantes antes de iniciar desenvolvimento.

Proximo passo recomendado: validar perguntas abertas com o responsavel do
produto, atualizar requisitos e executar revisao de completude com
`review-spec-completeness`.
"""


def render_functional_spec(context: dict) -> str:
    return f"""# Especificacao Funcional: {context['title']}

## Fatos E Decisoes

{render_bullets(context['decisions'])}

## Regras De Negocio

- Regras confirmadas devem prevalecer sobre inferencias de codigo.
- Qualquer lacuna remanescente deve voltar para entrevista antes da entrega.

## Criterios De Aceite

- Dado um usuario autorizado, quando executar a jornada principal, entao o
  sistema deve registrar o resultado esperado.
- Dado um usuario sem permissao, quando tentar executar a acao, entao o sistema
  deve bloquear e registrar o motivo.
"""


def render_technical_spec(context: dict) -> str:
    return f"""# Especificacao Tecnica: {context['title']}

## Base Tecnica

Derivar componentes, APIs, dados, permissoes e testes a partir da analise
refinada.

## Impactos

- Validar componentes impactados antes da implementacao.
- Confirmar contratos externos, migrations e permissoes.

## Testes

- Unitarios para regras.
- Integracao para contratos.
- E2E para jornada principal.
- Regressao para status e permissoes.
"""


def render_user_stories(context: dict) -> str:
    return f"""# User Stories: {context['title']}

## US-001

Como usuario autorizado, quero executar a jornada confirmada na analise, para
atingir o resultado esperado do processo.

### Criterios De Aceite

- Dado que tenho permissao, quando executo a acao principal, entao o sistema
  conclui a jornada.
- Dado que falta informacao obrigatoria, quando tento concluir, entao o sistema
  informa o que precisa ser corrigido.
"""


def render_journey_flows(context: dict) -> str:
    return f"""# Jornadas E Fluxogramas: {context['title']}

```mermaid
flowchart TD
    A[Inicio] --> B[Usuario autorizado acessa a funcionalidade]
    B --> C[Sistema valida dados e permissoes]
    C --> D{{Validacao aprovada?}}
    D -->|Sim| E[Sistema registra resultado]
    D -->|Nao| F[Sistema informa pendencias]
    F --> B
    E --> G[Fim]
```
"""


def render_traceability(context: dict) -> str:
    return f"""# Matriz De Rastreabilidade: {context['title']}

| Requisito | Historia | Criterio | Fonte | Status |
|---|---|---|---|---|
| RF-001 | US-001 | CA-001 | Analise refinada | Pronto para refinamento tecnico |
| RF-002 | US-001 | CA-002 | Feedback | Pronto para QA |
"""


def render_open_questions(context: dict) -> str:
    questions = context['questions']
    return f"""# Perguntas Abertas: {context['title']}

## Perguntas Derivadas Da Analise

{render_bullets(questions) if questions else '- Nenhuma pergunta aberta identificada na analise.'}
"""


def read_markdown_dir(directory: Path) -> str:
    chunks = []
    for file in sorted(directory.glob("*.md")):
        chunks.append(f"# Fonte: {file.name}\n\n{file.read_text(encoding='utf-8')}")
    return "\n\n".join(chunks)


def extract_decisions(text: str) -> list[str]:
    decisions = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("- ").strip()
        if stripped and not stripped.startswith("#") and not stripped.endswith("?") and len(stripped) > 12:
            decisions.append(stripped)
    return decisions[:20]


def extract_questions(text: str) -> list[str]:
    return [line.strip().lstrip("- ").strip() for line in text.splitlines() if line.strip().endswith("?")]


def infer_title(text: str, fallback: Path) -> str:
    generic = {
        "analise refinada",
        "registro de decisoes",
        "perguntas resolvidas",
        "perguntas ainda abertas",
        "fonte: refined-analysis.md",
        "fonte: decision-log.md",
    }
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            lowered = title.lower()
            if title and lowered not in generic and not lowered.startswith("fonte:") and not lowered.startswith("analise refinada:"):
                return title
            if lowered.startswith("analise refinada:"):
                return title.split(":", 1)[1].strip()
    return fallback.name.replace("-", " ").replace("_", " ").title()


def normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return re.sub(r"[^a-zA-Z0-9]+", "", normalized.encode("ascii", "ignore").decode("ascii")).lower()


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", normalize(value)).strip("-") or "final-spec"


def resolve_output_dir(output_dir: str | None, slug: str) -> Path:
    return Path(output_dir).expanduser().resolve() if output_dir else Path.cwd() / "specifications" / slug


def ensure_output_dir(output_dir: Path, yes_create_dir: bool) -> None:
    if output_dir.exists():
        if not output_dir.is_dir():
            raise ValueError(f"output path exists and is not a directory: {output_dir}")
        return
    if not yes_create_dir:
        answer = input(f"Criar pasta de especificacao final em {output_dir}? [s/N] ").strip().lower()
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
    print(f"Especificacao final gerada em: {output_dir}")
    print("")
    for name in documents:
        print(f"- {output_dir / name}")


def render_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- Nenhum item identificado."


if __name__ == "__main__":
    raise SystemExit(main())
