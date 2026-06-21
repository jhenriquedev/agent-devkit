#!/usr/bin/env python3
"""Runner for software-specification-analyst/analyze-project-context."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys


IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".next",
    ".venv",
    "__pycache__",
    "bin",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "obj",
    "target",
    "vendor",
}

INTERESTING_NAMES = {
    "README.md",
    "AGENTS.md",
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "pom.xml",
    "build.gradle",
    "Cargo.toml",
    "go.mod",
    "docker-compose.yml",
    "Dockerfile",
    ".env.example",
}

INTERESTING_SUFFIXES = {
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".md",
    ".php",
    ".py",
    ".rb",
    ".sql",
    ".swift",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}

ARTIFACTS = {
    "analysis-context.md": "render_analysis_context",
    "project-architecture-notes.md": "render_architecture_notes",
    "business-rules-discovered.md": "render_business_rules",
    "critical-points.md": "render_critical_points",
    "business-questions.md": "render_business_questions",
    "technical-impact-analysis.md": "render_technical_impact",
    "integration-map.md": "render_integration_map",
    "data-and-permissions-analysis.md": "render_data_permissions",
    "open-decisions.md": "render_open_decisions",
    "analysis-review.md": "render_analysis_review",
}


@dataclass(frozen=True)
class ProjectSnapshot:
    project: Path
    depth: str
    focus: str | None
    files: list[Path]
    documentation: list[Path]
    manifests: list[Path]
    source_files: list[Path]
    test_files: list[Path]
    config_files: list[Path]
    directories: list[Path]
    observed_terms: list[str]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run software-specification-analyst/analyze-project-context"
    )
    parser.add_argument("--project", required=True, help="diretorio do projeto a analisar")
    parser.add_argument("--output-dir", help="diretorio onde os artefatos serao salvos")
    parser.add_argument("--depth", choices=["light", "medium", "deep"], help="profundidade da analise")
    parser.add_argument("--focus", help="recorte funcional ou tecnico da analise")
    parser.add_argument("--yes-create-dir", action="store_true")
    parser.add_argument("--yes-overwrite", action="store_true")
    args = parser.parse_args()

    try:
        project = Path(args.project).expanduser().resolve()
        if not project.exists() or not project.is_dir():
            raise ValueError(f"project directory not found: {project}")

        snapshot = inspect_project(project, args.depth or "medium", args.focus)
        output_dir = resolve_output_dir(args.output_dir, project)
        ensure_output_dir(output_dir, args.yes_create_dir)
        documents = render_documents(snapshot)
        write_documents(output_dir, documents, args.yes_overwrite)
        print_summary(output_dir, documents)
    except KeyboardInterrupt:
        print("\nOperacao cancelada.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def inspect_project(project: Path, depth: str, focus: str | None) -> ProjectSnapshot:
    max_files = {"light": 80, "medium": 220, "deep": 600}[depth]
    files: list[Path] = []
    directories: set[Path] = set()

    for path in sorted(project.rglob("*")):
        relative = path.relative_to(project)
        parts = set(relative.parts)
        if parts & IGNORED_DIRS:
            continue
        if path.is_dir():
            directories.add(relative)
            continue
        if not should_include_file(path):
            continue
        files.append(relative)
        if len(files) >= max_files:
            break

    documentation = [path for path in files if path.suffix.lower() == ".md"]
    manifests = [path for path in files if path.name in INTERESTING_NAMES]
    source_files = [path for path in files if path.suffix.lower() in {".cs", ".go", ".java", ".js", ".jsx", ".kt", ".php", ".py", ".rb", ".swift", ".ts", ".tsx"}]
    test_files = [path for path in files if is_test_file(path)]
    config_files = [path for path in files if path.suffix.lower() in {".json", ".toml", ".yaml", ".yml"} or path.name.startswith(".env")]
    observed_terms = extract_observed_terms(project, documentation + source_files[:20])

    return ProjectSnapshot(
        project=project,
        depth=depth,
        focus=focus,
        files=files,
        documentation=documentation,
        manifests=manifests,
        source_files=source_files,
        test_files=test_files,
        config_files=config_files,
        directories=sorted(directories),
        observed_terms=observed_terms,
    )


def should_include_file(path: Path) -> bool:
    if path.name in INTERESTING_NAMES:
        return True
    if path.suffix.lower() not in INTERESTING_SUFFIXES:
        return False
    try:
        return path.stat().st_size <= 400_000
    except OSError:
        return False


def is_test_file(path: Path) -> bool:
    lowered = str(path).lower()
    return (
        "/test" in lowered
        or "\\test" in lowered
        or path.name.lower().startswith("test_")
        or ".test." in path.name.lower()
        or ".spec." in path.name.lower()
    )


def extract_observed_terms(project: Path, files: list[Path]) -> list[str]:
    terms: dict[str, int] = {}
    for relative in files[:30]:
        path = project / relative
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for raw in re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9_-]{4,}", text):
            term = raw.strip("_-").lower()
            if term in {"function", "return", "const", "class", "import", "export", "string", "latest"}:
                continue
            terms[term] = terms.get(term, 0) + 1
    return [term for term, _count in sorted(terms.items(), key=lambda item: (-item[1], item[0]))[:20]]


def resolve_output_dir(output_dir: str | None, project: Path) -> Path:
    if output_dir:
        return Path(output_dir).expanduser().resolve()
    return Path.cwd() / "specifications" / f"{slugify(project.name)}-analysis"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "project"


def ensure_output_dir(output_dir: Path, yes_create_dir: bool) -> None:
    if output_dir.exists():
        if not output_dir.is_dir():
            raise ValueError(f"output path exists and is not a directory: {output_dir}")
        return
    if not yes_create_dir:
        print("Posso criar a pasta de analise neste projeto?")
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
    print(f"Documentos de analise gerados em: {output_dir}")
    print("")
    for name in documents:
        print(f"- {output_dir / name}")


def render_documents(snapshot: ProjectSnapshot) -> dict[str, str]:
    renderers = {
        "render_analysis_context": render_analysis_context,
        "render_architecture_notes": render_architecture_notes,
        "render_business_rules": render_business_rules,
        "render_critical_points": render_critical_points,
        "render_business_questions": render_business_questions,
        "render_technical_impact": render_technical_impact,
        "render_integration_map": render_integration_map,
        "render_data_permissions": render_data_permissions,
        "render_open_decisions": render_open_decisions,
        "render_analysis_review": render_analysis_review,
    }
    return {name: renderers[renderer](snapshot) for name, renderer in ARTIFACTS.items()}


def render_analysis_context(snapshot: ProjectSnapshot) -> str:
    return f"""# Contexto De Analise: {snapshot.project.name}

## Escopo

- Projeto analisado: `{snapshot.project.name}`
- Caminho: `{snapshot.project}`
- Profundidade: `{snapshot.depth}`
- Foco: {snapshot.focus or "nao informado"}

## Fatos Observados No Projeto

- Arquivos considerados: {len(snapshot.files)}
- Diretorios considerados: {len(snapshot.directories)}
- Documentos encontrados: {len(snapshot.documentation)}
- Manifests/configuracoes relevantes: {len(snapshot.manifests)}
- Arquivos de codigo encontrados: {len(snapshot.source_files)}
- Arquivos de teste encontrados: {len(snapshot.test_files)}

## Arquivos Relevantes

{render_path_list(snapshot.files[:40])}

## Termos Observados

{render_term_list(snapshot.observed_terms)}

## Inferencias

- A estrutura encontrada sugere pontos para entrevista e validacao de negocio.
- Termos recorrentes no codigo ou documentacao devem ser confirmados como
  conceitos de negocio antes de virarem requisitos.

## Proximo Passo Recomendado

Revisar `business-questions.md` e `critical-points.md` com stakeholders antes
de criar a especificacao final.
"""


def render_architecture_notes(snapshot: ProjectSnapshot) -> str:
    return f"""# Notas De Arquitetura: {snapshot.project.name}

## Estrutura Observada

{render_path_list(snapshot.directories[:60])}

## Manifests E Configuracoes

{render_path_list(snapshot.manifests + snapshot.config_files[:20])}

## Codigo

{render_path_list(snapshot.source_files[:60])}

## Testes

{render_path_list(snapshot.test_files[:40])}

## Lacunas Arquiteturais

- Confirmar camadas, ownership e fronteiras reais do sistema.
- Confirmar se os arquivos encontrados representam a jornada completa ou apenas
  uma parte do dominio.
"""


def render_business_rules(snapshot: ProjectSnapshot) -> str:
    return f"""# Regras De Negocio Descobertas: {snapshot.project.name}

## Fatos Observados

- O projeto contem termos que podem representar conceitos de negocio:
  {", ".join(snapshot.observed_terms[:12]) if snapshot.observed_terms else "nenhum termo recorrente identificado"}.

## Inferencias Provaveis

- Nomes de arquivos, funcoes e documentos podem indicar regras existentes, mas
  nao confirmam intencao de negocio.

## Regras Confirmadas

- Nenhuma regra de negocio deve ser considerada confirmada apenas pela analise
  estatica do codigo.

## Perguntas Para Validacao

- Quais desses termos representam entidades ou processos oficiais do negocio?
- Quais comportamentos do codigo sao regra obrigatoria e quais sao apenas
  implementacao historica?
"""


def render_critical_points(snapshot: ProjectSnapshot) -> str:
    missing_tests = "sim" if snapshot.source_files and not snapshot.test_files else "nao"
    return f"""# Pontos Criticos: {snapshot.project.name}

| Ponto | Evidencia | Impacto | Acao Recomendada |
|---|---|---|---|
| Regras implicitas no codigo | Termos observados: {", ".join(snapshot.observed_terms[:6]) or "n/a"} | Medio | Validar com negocio antes de especificar. |
| Cobertura de testes ausente ou incompleta | Ausencia de testes para codigo: {missing_tests} | Alto se a mudanca for critica | Mapear cenarios de regressao. |
| Integracoes nao confirmadas | Analise estatica inicial | Medio | Confirmar sistemas externos e contratos. |
| Permissoes nao confirmadas | Analise estatica inicial | Alto se houver dados sensiveis | Validar papeis, autorizacoes e auditoria. |
"""


def render_business_questions(snapshot: ProjectSnapshot) -> str:
    terms = ", ".join(snapshot.observed_terms[:10]) if snapshot.observed_terms else "conceitos do dominio"
    return f"""# Perguntas De Negocio: {snapshot.project.name}

## Conceitos Observados

- Termos para validacao: {terms}

## Perguntas Bloqueantes

- Quais termos observados no projeto representam entidades oficiais do negocio?
- Quais regras atuais foram intencionais e quais sao efeitos da implementacao?
- Quais fluxos sao obrigatorios para o usuario final?
- Quais excecoes devem bloquear, alertar ou permitir continuidade?
- Quais dados sao sensiveis e exigem auditoria?

## Perguntas De Escopo

- A demanda altera fluxo existente ou cria uma nova capacidade?
- Ha impacto em usuarios internos, externos ou administradores?
- A mudanca depende de outro projeto ou sistema externo?
"""


def render_technical_impact(snapshot: ProjectSnapshot) -> str:
    return f"""# Analise De Impacto Tecnico: {snapshot.project.name}

## Areas Possivelmente Impactadas

{render_path_list(snapshot.source_files[:50])}

## Testes E Qualidade

{render_path_list(snapshot.test_files[:30])}

## Riscos Tecnicos

- Mudancas em regras existentes podem quebrar fluxos nao documentados.
- A ausencia de testes proximos aos arquivos impactados aumenta risco de
  regressao.
- Contratos externos precisam ser identificados antes da estimativa.
"""


def render_integration_map(snapshot: ProjectSnapshot) -> str:
    possible_integrations = [
        path for path in snapshot.files
        if any(token in str(path).lower() for token in ("api", "client", "http", "integration", "connector", "repository"))
    ]
    return f"""# Mapa De Integracoes: {snapshot.project.name}

## Possiveis Pontos De Integracao

{render_path_list(possible_integrations[:50])}

## Perguntas

- Existem APIs, filas, jobs, arquivos ou webhooks envolvidos?
- Quem e dono dos contratos externos?
- Ha ambiente de homologacao e massa de testes disponivel?
"""


def render_data_permissions(snapshot: ProjectSnapshot) -> str:
    possible_data_files = [
        path for path in snapshot.files
        if any(token in str(path).lower() for token in ("model", "entity", "schema", "migration", "permission", "auth", "role", "user"))
    ]
    return f"""# Analise De Dados E Permissoes: {snapshot.project.name}

## Arquivos Possivelmente Relacionados

{render_path_list(possible_data_files[:50])}

## Pontos De Atencao

- Confirmar entidades, campos obrigatorios e retencao.
- Confirmar papeis, permissoes e segregacao de acesso.
- Identificar dados sensiveis antes de detalhar requisitos.
"""


def render_open_decisions(snapshot: ProjectSnapshot) -> str:
    return f"""# Decisoes Em Aberto: {snapshot.project.name}

| Decisao | Status | Dono Sugerido |
|---|---|---|
| Profundidade final da especificacao | {snapshot.depth} usado nesta analise | Produto/Analise |
| Regras de negocio confirmadas | Aberto | Negocio |
| Componentes realmente impactados | Aberto | Engenharia |
| Estrategia de testes e regressao | Aberto | QA/Engenharia |
| Permissoes e auditoria | Aberto | Produto/Seguranca |
"""


def render_analysis_review(snapshot: ProjectSnapshot) -> str:
    return f"""# Revisao Da Analise: {snapshot.project.name}

## Status

Analise inicial criada a partir de leitura estatica do projeto.

## O Que Pode Ser Usado Agora

- Contexto estrutural do projeto.
- Lista inicial de arquivos, termos e pontos de atencao.
- Perguntas de negocio para entrevista.

## O Que Ainda Precisa Validacao

- Regras de negocio reais.
- Fluxos de usuario.
- Dados sensiveis e permissoes.
- Contratos externos e impactos cross-project.

## Handoff

Recomenda-se revisar perguntas abertas antes de executar
`create-final-spec-from-analysis`.
"""


def render_path_list(paths: list[Path]) -> str:
    if not paths:
        return "- Nenhum item identificado."
    return "\n".join(f"- `{path}`" for path in paths)


def render_term_list(terms: list[str]) -> str:
    if not terms:
        return "- Nenhum termo recorrente identificado."
    return "\n".join(f"- {term}" for term in terms)


if __name__ == "__main__":
    raise SystemExit(main())
