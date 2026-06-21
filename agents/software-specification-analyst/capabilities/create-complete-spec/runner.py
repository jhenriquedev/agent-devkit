#!/usr/bin/env python3
"""Runner for software-specification-analyst/create-complete-spec."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
import unicodedata


ARTIFACTS = {
    "software-specification.md": "render_complete_spec",
    "functional-spec.md": "render_functional_spec",
    "technical-spec.md": "render_technical_spec",
    "user-stories.md": "render_user_stories",
    "journey-flows.md": "render_journey_flows",
    "requirements-traceability.md": "render_traceability",
    "open-questions.md": "render_open_questions",
}


@dataclass(frozen=True)
class SpecContext:
    title: str
    slug: str
    source_path: Path
    source_text: str


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run software-specification-analyst/create-complete-spec"
    )
    parser.add_argument("--input", required=True, help="arquivo Markdown/texto com a demanda")
    parser.add_argument("--title", help="titulo da especificacao")
    parser.add_argument("--output-dir", help="diretorio onde os artefatos serao salvos")
    parser.add_argument(
        "--yes-create-dir",
        action="store_true",
        help="cria o diretorio de saida sem pergunta interativa",
    )
    parser.add_argument(
        "--yes-overwrite",
        action="store_true",
        help="sobrescreve arquivos existentes sem pergunta interativa",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="imprime a especificacao completa em vez de salvar arquivos",
    )
    args = parser.parse_args()

    try:
        source_path = Path(args.input).expanduser().resolve()
        if not source_path.exists():
            raise ValueError(f"input not found: {source_path}")

        source_text = source_path.read_text(encoding="utf-8")
        title = args.title or infer_title(source_text, source_path)
        context = SpecContext(
            title=title,
            slug=slugify(title),
            source_path=source_path,
            source_text=source_text.strip(),
        )

        documents = render_documents(context)
        if args.stdout:
            print(documents["software-specification.md"], end="")
            return 0

        output_dir = resolve_output_dir(args.output_dir, context.slug)
        ensure_output_dir(output_dir, args.yes_create_dir)
        write_documents(output_dir, documents, args.yes_overwrite)
        print_summary(output_dir, documents)
    except KeyboardInterrupt:
        print("\nOperacao cancelada.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def infer_title(source_text: str, source_path: Path) -> str:
    for line in source_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            if title:
                return title
        if stripped:
            return stripped[:80]
    return source_path.stem.replace("-", " ").replace("_", " ").title()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return slug or "software-specification"


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
        print("Posso criar a pasta de especificacao neste projeto?")
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
        print("Os seguintes arquivos ja existem:")
        for name in existing:
            print(f"- {output_dir / name}")
        answer = input("Sobrescrever arquivos existentes? [s/N] ").strip().lower()
        if answer not in {"s", "sim", "y", "yes"}:
            raise ValueError("sobrescrita nao autorizada")

    for name, content in documents.items():
        (output_dir / name).write_text(content, encoding="utf-8")


def print_summary(output_dir: Path, documents: dict[str, str]) -> None:
    print("# Software Specification Analyst")
    print("")
    print(f"Artefatos gerados em: {output_dir}")
    print("")
    for name in documents:
        print(f"- {output_dir / name}")


def render_documents(context: SpecContext) -> dict[str, str]:
    renderers = {
        "render_complete_spec": render_complete_spec,
        "render_functional_spec": render_functional_spec,
        "render_technical_spec": render_technical_spec,
        "render_user_stories": render_user_stories,
        "render_journey_flows": render_journey_flows,
        "render_traceability": render_traceability,
        "render_open_questions": render_open_questions,
    }
    return {name: renderers[renderer](context) for name, renderer in ARTIFACTS.items()}


def render_complete_spec(context: SpecContext) -> str:
    return f"""# Especificacao De Software: {context.title}

## Resumo Executivo

Esta especificacao consolida a demanda fornecida em artefatos funcionais e
tecnicos para apoiar refinamento, desenvolvimento, QA e revisao de arquitetura.

## Fatos Fornecidos

{quote_source(context.source_text)}

## Inferencias

- A demanda precisa ser refinada com stakeholders antes de implementacao.
- Os requisitos abaixo devem ser validados contra o contexto real do produto.

## Premissas

- O projeto atual e o local correto para armazenar a especificacao.
- Nao ha decisoes tecnicas obrigatorias alem das explicitamente informadas.

## Contexto E Problema

A definir a partir da validacao da demanda.

## Objetivos

- Transformar a demanda em contrato implementavel.
- Reduzir ambiguidades antes do desenvolvimento.
- Criar base para user stories, testes e handoff tecnico.

## Escopo

- Documentar requisitos funcionais e nao funcionais.
- Documentar fluxos, criterios de aceite e matriz de rastreabilidade.
- Registrar riscos, dependencias e perguntas abertas.

## Fora De Escopo

- Implementar codigo da solucao.
- Executar alteracoes em sistemas externos.
- Fechar decisoes de produto sem confirmacao.

## Atores E Personas

| Ator | Objetivo | Observacoes |
|---|---|---|
| Usuario final | A definir | Confirmar perfil e necessidades. |
| Operador interno | A definir | Confirmar se existe operacao manual. |
| Administrador | A definir | Confirmar permissoes e governanca. |

## Requisitos Funcionais

| ID | Requisito | Fonte | Status |
|---|---|---|---|
| RF-001 | O sistema deve atender a capacidade descrita na demanda. | Entrada | Precisa detalhar |

## Requisitos Nao Funcionais

| ID | Requisito | Status |
|---|---|---|
| RNF-001 | Definir requisitos de seguranca, auditoria e permissao. | Aberto |
| RNF-002 | Definir requisitos de desempenho e disponibilidade. | Aberto |
| RNF-003 | Definir requisitos de observabilidade e suporte. | Aberto |

## Regras De Negocio

- A definir com stakeholders de negocio.

## User Stories

Consulte `user-stories.md`.

## Criterios De Aceite

- Cada requisito funcional deve ter ao menos um criterio de aceite verificavel.
- Cenarios de excecao devem ser cobertos antes da implementacao.

## Jornadas E Fluxogramas

Consulte `journey-flows.md`.

## Modelo De Dados

- Entidades, atributos obrigatorios, retencao e classificacao de dados ainda
  precisam ser definidos.

## APIs E Integracoes

- APIs, eventos, jobs e sistemas externos ainda precisam ser confirmados.

## Permissoes E Seguranca

- Definir autenticacao, autorizacao, segregacao de papeis e dados sensiveis.

## Observabilidade

- Definir logs, metricas, traces, auditoria e alertas relevantes.

## Estrategia De Testes

- Testes unitarios para regras isoladas.
- Testes de integracao para contratos externos.
- Testes E2E para jornadas principais.
- Testes de regressao para fluxos criticos.

## Riscos E Dependencias

| Risco | Impacto | Mitigacao |
|---|---|---|
| Requisitos incompletos | Alto | Resolver perguntas abertas antes de construir. |
| Regras de negocio implicitas | Alto | Validar regras com responsavel do produto. |

## Matriz De Rastreabilidade

Consulte `requirements-traceability.md`.

## Perguntas Abertas

Consulte `open-questions.md`.

## Handoff Para Desenvolvimento

Status: precisa de refinamento antes da implementacao.

Proximo passo recomendado: validar perguntas abertas, atualizar requisitos e
executar revisao de completude.
"""


def render_functional_spec(context: SpecContext) -> str:
    return f"""# Especificacao Funcional: {context.title}

## Contexto

{quote_source(context.source_text)}

## Problema

A definir com base no impacto esperado para usuarios e operacao.

## Objetivos

- Descrever comportamento esperado do produto.
- Explicitar regras de negocio e excecoes.
- Apoiar escrita de historias e criterios de aceite.

## Escopo

- Capacidade descrita na demanda.
- Fluxos principais, alternativos e excecoes.

## Fora De Escopo

- Decisoes tecnicas nao confirmadas.
- Implementacao.

## Atores E Personas

| Ator | Necessidade | Pergunta aberta |
|---|---|---|
| Usuario final | A definir | Quem usa a funcionalidade? |

## Requisitos Funcionais

| ID | Requisito | Criterio De Aceite |
|---|---|---|
| RF-001 | Atender a demanda descrita. | Validar comportamento esperado. |

## Regras De Negocio

- A definir.

## Fluxos E Excecoes

- Fluxo principal: a definir.
- Fluxos alternativos: a definir.
- Excecoes: a definir.

## Criterios De Aceite

- Devem ser objetivos, verificaveis e rastreaveis para os requisitos.

## Perguntas Abertas

- Qual e o usuario principal?
- Quais regras de negocio sao obrigatorias?
- Quais excecoes devem bloquear a jornada?
"""


def render_technical_spec(context: SpecContext) -> str:
    return f"""# Especificacao Tecnica: {context.title}

## Resumo Tecnico

A arquitetura definitiva depende das respostas funcionais e do contexto do
sistema atual.

## Arquitetura

- Componentes impactados: a definir.
- Fronteiras de servico: a definir.
- Estados e transicoes: a definir.

## Componentes

| Componente | Responsabilidade | Status |
|---|---|---|
| A definir | A definir | Aberto |

## Modelo De Dados

- Entidades e atributos ainda nao confirmados.
- Classificacao de dados sensiveis deve ser avaliada.

## APIs

- Endpoints, contratos, erros e versionamento precisam ser definidos se houver
  API.

## Integracoes

- Sistemas externos e protocolos precisam ser confirmados.

## Seguranca

- Autenticacao: a definir.
- Autorizacao: a definir.
- Auditoria: a definir.
- Dados sensiveis: a avaliar.

## Observabilidade

- Logs de eventos de negocio.
- Metricas de sucesso, falha e latencia.
- Alertas para falhas operacionais.

## Rollout E Rollback

- Definir estrategia de feature flag, migracao e rollback quando houver impacto
  em producao.

## Estrategia De Testes

- Unitarios: regras de negocio.
- Integracao: APIs, banco e servicos externos.
- E2E: jornada principal.
- Regressao: fluxos criticos existentes.

## Riscos Tecnicos

- Falta de contexto de arquitetura atual.
- Falta de definicao de dados e integracoes.

## Decisoes Em Aberto

- Stack, componentes e contratos externos.
"""


def render_user_stories(context: SpecContext) -> str:
    return f"""# User Stories: {context.title}

## Epicos

| ID | Epico | Objetivo |
|---|---|---|
| EP-001 | Entregar capacidade solicitada | Resolver a demanda descrita. |

## Features

| ID | Feature | Epico |
|---|---|---|
| FT-001 | Funcionalidade principal | EP-001 |

## Historias

### US-001

Como usuario da solucao, quero executar a capacidade descrita na demanda, para
atingir o resultado esperado do produto.

#### Criterios De Aceite

- Dado que o usuario tem permissao para usar a funcionalidade
- Quando ele executa a jornada principal
- Entao o sistema deve concluir o fluxo esperado

#### Dependencias

- Definir ator principal.
- Definir regras de negocio.
- Definir dados e integracoes.

#### Perguntas Abertas

- Quem e o usuario da historia?
- Qual resultado comprova sucesso?
- Quais excecoes devem ser cobertas?
"""


def render_journey_flows(context: SpecContext) -> str:
    return f"""# Jornadas E Fluxogramas: {context.title}

## Jornada Principal

```mermaid
flowchart TD
    A[Inicio] --> B[Usuario acessa a funcionalidade]
    B --> C[Sistema apresenta entrada ou contexto necessario]
    C --> D[Usuario executa acao principal]
    D --> E[Sistema valida regras]
    E --> F[Resultado entregue]
    F --> G[Fim]
```

## Fluxos Alternativos

```mermaid
flowchart TD
    A[Validacao de regras] --> B{{Dados validos?}}
    B -->|Sim| C[Continuar fluxo principal]
    B -->|Nao| D[Exibir erro acionavel]
    D --> E[Usuario corrige entrada]
    E --> A
```

## Excecoes

- Falta de permissao.
- Dados invalidos ou incompletos.
- Falha em integracao externa.

## Perguntas Abertas

- Quais passos reais compoem a jornada?
- Quais erros devem ser recuperaveis?
- Quais erros encerram o processo?
"""


def render_traceability(context: SpecContext) -> str:
    return f"""# Matriz De Rastreabilidade: {context.title}

| Requisito | Historia | Criterio De Aceite | Componente | Teste | Risco | Status |
|---|---|---|---|---|---|---|
| RF-001 | US-001 | CA-001 | A definir | E2E da jornada principal | Requisito amplo demais | Aberto |
| RNF-001 | A definir | A definir | Seguranca | Testes de permissao | Permissao indefinida | Aberto |
| RNF-002 | A definir | A definir | Observabilidade | Validacao de logs e metricas | Falha sem diagnostico | Aberto |
"""


def render_open_questions(context: SpecContext) -> str:
    return f"""# Perguntas Abertas: {context.title}

## Produto

- Qual problema de negocio precisa ser resolvido?
- Qual resultado mensuravel indica sucesso?
- Quem e o usuario principal?

## Funcional

- Quais regras de negocio sao obrigatorias?
- Quais excecoes devem existir?
- Quais campos, estados ou acoes sao obrigatorios?

## Tecnico

- Quais sistemas, APIs ou bancos serao impactados?
- Existem requisitos de seguranca, auditoria ou compliance?
- Ha restricoes de performance, disponibilidade ou rollout?

## QA

- Quais cenarios sao criticos para regressao?
- Quais dados de teste representam a jornada real?
"""


def quote_source(source_text: str) -> str:
    if not source_text:
        return "> Nenhum conteudo fornecido."
    lines = [line.rstrip() for line in source_text.splitlines()]
    return "\n".join(f"> {line}" if line else ">" for line in lines)


if __name__ == "__main__":
    raise SystemExit(main())
