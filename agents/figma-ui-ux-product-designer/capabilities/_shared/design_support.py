"""Shared runners for figma-ui-ux-product-designer capabilities."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from typing import Any


AGENT_DIR = Path(__file__).resolve().parents[2]
ROOT = AGENT_DIR.parents[1]
FIGMA_INFRA_DIR = AGENT_DIR / "infra" / "integrations" / "figma"
sys.path.insert(0, str(FIGMA_INFRA_DIR))

from figma_mcp_adapter import FigmaMcpAdapter  # noqa: E402
from figma_mode import detect_mode, merged_env, read_env_file  # noqa: E402
from figma_models import FigmaOperation  # noqa: E402
from figma_operation_log import write_execution_artifacts  # noqa: E402

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
TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".json", ".yaml", ".yml", ".csv", ".html", ".css", ".js", ".jsx", ".ts", ".tsx"}
DOCUMENT_SUFFIXES = TEXT_SUFFIXES | {".pdf", ".docx", ".xlsx"}

CAPABILITY_TITLES = {
    "conduct-design-interview": "Design Interview",
    "ingest-design-source": "Design Source Ingestion",
    "read-azure-card-for-design": "Azure Card Design Context",
    "analyze-product-context": "Product Context Analysis",
    "analyze-existing-figma-project": "Existing Figma Project Analysis",
    "create-figma-project": "Figma Project Plan",
    "create-design-system-foundation": "Design System Foundation",
    "create-mobile-app-design": "Mobile App Design",
    "create-web-app-design": "Web App Design",
    "capture-url-to-figma": "URL To Figma Capture",
    "recreate-legacy-design": "Legacy Design Recreation",
    "facelift-existing-product": "Product Facelift",
    "update-existing-figma-design": "Existing Figma Design Update",
    "triage-design-feedback": "Design Feedback Triage",
    "apply-design-feedback": "Design Feedback Application",
    "conduct-design-review-session": "Design Review Session",
    "generate-user-journey-diagram": "User Journey Diagram",
    "generate-dev-handoff": "Developer Handoff",
    "review-design-quality": "Design Quality Review",
}

FIGMA_EXECUTION_OPERATIONS = {
    "analyze-existing-figma-project",
    "apply-design-feedback",
    "capture-url-to-figma",
    "create-design-system-foundation",
    "create-figma-project",
    "create-mobile-app-design",
    "create-web-app-design",
    "facelift-existing-product",
    "recreate-legacy-design",
    "review-design-quality",
    "update-existing-figma-design",
}

FIGMA_WRITE_OPERATIONS = {
    "apply-design-feedback",
    "capture-url-to-figma",
    "create-design-system-foundation",
    "create-figma-project",
    "create-mobile-app-design",
    "create-web-app-design",
    "facelift-existing-product",
    "recreate-legacy-design",
    "update-existing-figma-design",
}


@dataclass(frozen=True)
class SourceItem:
    path: str
    kind: str
    text: str
    warning: str | None = None


def run(operation: str) -> int:
    parser = build_parser(operation)
    args = parser.parse_args()
    try:
        source_items = load_sources(args.source)
        brief_text = load_optional_text(args.brief)
        feedback_text = load_optional_text(args.feedback)
        figma_mode = detect_figma_mode(args.require_direct)
        context = {
            "operation": operation,
            "title": CAPABILITY_TITLES.get(operation, operation.replace("-", " ").title()),
            "brief": brief_text,
            "feedback": feedback_text,
            "sources": source_items,
            "figma_mode": figma_mode,
            "figma_file_url": args.figma_file_url,
            "figma_project_url": args.figma_project_url,
            "url": args.url,
            "azure_card": args.azure_card,
            "platform": args.platform,
            "scope": args.scope,
            "target_audience": args.target_audience,
            "design_style": args.design_style,
            "depth": resolve_depth(args.depth, source_items, brief_text, operation),
            "vendor_skills": select_vendor_skills(operation),
            "figma_execution": None,
        }
        if figma_mode["mode"] == "blocked":
            raise ValueError(figma_mode["reason"])
        if args.stdout:
            documents = render_documents(context)
            print(documents["design-brief.md"], end="")
            return 0
        output_dir = resolve_output_dir(args.output_dir, operation, context["depth"]["slug"])
        ensure_output_dir(output_dir, args.yes_create_dir)
        if should_execute_figma(operation, figma_mode):
            require_figma_write_confirmation(operation, args.yes_figma_write)
            execution = execute_figma_operation(operation, args, context)
            context["figma_execution"] = execution
            write_execution_artifacts(output_dir, execution)
        documents = render_documents(context)
        write_documents(output_dir, documents, args.yes_overwrite)
        print_summary(output_dir, documents, figma_mode)
    except KeyboardInterrupt:
        print("\nOperacao cancelada.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def build_parser(operation: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"Run figma-ui-ux-product-designer/{operation}")
    parser.add_argument("--source", action="append", default=[], help="arquivo ou pasta de contexto")
    parser.add_argument("--brief", help="arquivo de brief, requisito ou especificacao")
    parser.add_argument("--feedback", help="arquivo com feedback/comentarios")
    parser.add_argument("--output-dir")
    parser.add_argument("--stdout", action="store_true")
    parser.add_argument("--yes-create-dir", action="store_true")
    parser.add_argument("--yes-overwrite", action="store_true")
    parser.add_argument("--require-direct", action="store_true", help="falha se Figma direct_mcp nao estiver disponivel")
    parser.add_argument("--figma-file-url")
    parser.add_argument("--figma-project-url")
    parser.add_argument("--figma-file-name", help="nome do novo arquivo Figma quando aplicavel")
    parser.add_argument("--figma-page", default="AI DevKit Design", help="pagina alvo no Figma")
    parser.add_argument("--figma-node-id", help="node/frame alvo para atualizacoes")
    parser.add_argument("--figma-plan-key", help="planKey Figma quando o bridge exigir")
    parser.add_argument("--yes-figma-write", action="store_true", help="confirma criacao/alteracao real no Figma")
    parser.add_argument("--url", help="URL de app/site para captura ou benchmark")
    parser.add_argument("--azure-card", help="identificador do card Azure DevOps")
    parser.add_argument("--platform", choices=["web", "mobile", "both"], default="both")
    parser.add_argument("--scope", default="auto", help="tela, fluxo, modulo, produto ou auto")
    parser.add_argument("--target-audience")
    parser.add_argument("--design-style")
    parser.add_argument("--depth", choices=["light", "medium", "deep"])
    return parser


def detect_figma_mode(require_direct: bool) -> dict[str, str]:
    return detect_mode(ROOT, require_direct).as_dict()


def should_execute_figma(operation: str, figma_mode: dict[str, str]) -> bool:
    return figma_mode["mode"] == "direct_mcp" and operation in FIGMA_EXECUTION_OPERATIONS


def require_figma_write_confirmation(operation: str, yes_figma_write: bool) -> None:
    if operation not in FIGMA_WRITE_OPERATIONS:
        return
    if yes_figma_write:
        return
    print("Esta capability vai criar ou alterar conteudo real no Figma.")
    answer = input("Autoriza escrita no Figma? [s/N] ").strip().lower()
    if answer not in {"s", "sim", "y", "yes"}:
        raise ValueError("escrita no Figma nao autorizada")


def execute_figma_operation(operation: str, args: argparse.Namespace, context: dict[str, Any]) -> dict[str, Any]:
    env = merged_env(ROOT)
    command = env.get("FIGMA_MCP_BRIDGE_COMMAND", "")
    timeout = parse_int(env.get("FIGMA_MCP_BRIDGE_TIMEOUT_SECONDS"), 120)
    adapter = FigmaMcpAdapter(command=command, project_root=ROOT, timeout_seconds=timeout)
    operation_payload = build_figma_operation(operation, args, context, env)
    return adapter.execute(operation_payload)


def build_figma_operation(
    operation: str,
    args: argparse.Namespace,
    context: dict[str, Any],
    env: dict[str, str],
) -> FigmaOperation:
    file_name = args.figma_file_name or default_figma_file_name(context)
    page_name = args.figma_page or default_figma_page(operation)
    file_key = extract_figma_file_key(args.figma_file_url)
    action = action_for_operation(operation, bool(file_key))
    return FigmaOperation(
        capability=operation,
        action=action,
        file_name=file_name,
        page_name=page_name,
        platform=context["platform"],
        scope=context["scope"],
        screens=infer_screens(context),
        components=infer_components(context),
        brief=context["brief"],
        feedback=context["feedback"],
        figma_file_url=args.figma_file_url,
        figma_project_url=args.figma_project_url,
        figma_file_key=file_key,
        figma_node_id=args.figma_node_id,
        plan_key=args.figma_plan_key or env.get("FIGMA_DEFAULT_PLAN_KEY"),
        url=args.url,
        design_style=args.design_style,
        target_audience=args.target_audience,
        source_summaries=[
            {"path": item.path, "kind": item.kind, "preview": item.text[:600]}
            for item in context["sources"][:12]
        ],
    )


def default_figma_file_name(context: dict[str, Any]) -> str:
    title = context["title"]
    source_hint = first_non_empty_line(context["brief"]) or context["scope"] or "Design"
    return f"{title} - {source_hint[:48]}".strip()


def default_figma_page(operation: str) -> str:
    if operation == "create-design-system-foundation":
        return "Design System"
    if operation in {"review-design-quality", "conduct-design-review-session"}:
        return "Review"
    if operation in {"generate-user-journey-diagram", "analyze-product-context"}:
        return "Flows"
    return "AI DevKit Design"


def first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip().strip("#").strip()
        if stripped:
            return stripped
    return ""


def extract_figma_file_key(url: str | None) -> str | None:
    if not url:
        return None
    match = re.search(r"figma\.com/(?:file|design|board|slides)/([^/?#]+)", url)
    return match.group(1) if match else None


def action_for_operation(operation: str, has_file_key: bool) -> str:
    if operation == "analyze-existing-figma-project":
        return "inspect_file"
    if operation == "review-design-quality":
        return "review_file"
    if operation in {"update-existing-figma-design", "apply-design-feedback"}:
        return "update_screen"
    if operation == "capture-url-to-figma":
        return "capture_url_to_figma"
    if operation == "create-figma-project":
        return "create_file"
    if operation == "create-design-system-foundation":
        return "create_design_system"
    if operation in {"facelift-existing-product", "recreate-legacy-design"}:
        return "create_versioned_redesign" if has_file_key else "create_recreation_file"
    return "update_or_create_screen" if has_file_key else "create_file_with_screens"


def parse_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value else default
    except ValueError:
        return default


def load_sources(paths: list[str]) -> list[SourceItem]:
    items: list[SourceItem] = []
    for raw in paths:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            raise ValueError(f"source not found: {path}")
        if path.is_dir():
            items.extend(load_directory(path))
        else:
            items.append(load_file(path))
    return items


def load_directory(directory: Path) -> list[SourceItem]:
    items: list[SourceItem] = []
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        if set(relative.parts) & IGNORED_DIRS:
            continue
        if path.is_dir() or path.suffix.lower() not in DOCUMENT_SUFFIXES:
            continue
        if len(items) >= 80:
            break
        try:
            items.append(load_file(path))
        except ValueError:
            continue
    return items


def load_file(path: Path) -> SourceItem:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        if suffix == ".csv":
            return SourceItem(str(path), "csv", read_csv_summary(path))
        return SourceItem(str(path), suffix.lstrip(".") or "text", path.read_text(encoding="utf-8", errors="ignore")[:12000])
    if suffix == ".docx":
        return SourceItem(str(path), "docx", read_docx_text(path)[:12000])
    if suffix == ".xlsx":
        return SourceItem(str(path), "xlsx", read_xlsx_summary(path)[:12000])
    if suffix == ".pdf":
        text = read_pdf_text(path)
        warning = None if text else "PDF sem extrator disponivel no runtime; arquivo inventariado para leitura assistida."
        return SourceItem(str(path), "pdf", text[:12000] if text else f"PDF file: {path.name}", warning)
    raise ValueError(f"unsupported source format: {suffix}")


def read_csv_summary(path: Path) -> str:
    with path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))
    preview = rows[:12]
    return "\n".join(" | ".join(str(cell) for cell in row) for row in preview)


def read_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    texts = [node.text or "" for node in root.iter() if node.tag.endswith("}t")]
    return "\n".join(text for text in texts if text.strip())


def read_xlsx_summary(path: Path) -> str:
    if not zipfile.is_zipfile(path):
        return f"Workbook file: {path.name}"
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        worksheets = [name for name in names if name.startswith("xl/worksheets/")]
    return f"Workbook: {path.name}\nWorksheets detected: {len(worksheets)}\nParts: {len(names)}"


def read_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception:
            return ""
    try:
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception:
        return ""


def load_optional_text(path_value: str | None) -> str:
    if not path_value:
        return ""
    path = Path(path_value).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"file not found: {path}")
    return load_file(path).text


def resolve_depth(requested: str | None, sources: list[SourceItem], brief: str, operation: str) -> dict[str, str]:
    if requested:
        depth = requested
        reason = "Profundidade informada explicitamente."
    elif operation in {"facelift-existing-product", "recreate-legacy-design", "create-design-system-foundation"}:
        depth = "deep"
        reason = "Operacao exige comparacao, estrategia visual e revisao ampla."
    elif len(sources) > 15 or len(brief) > 4000:
        depth = "deep"
        reason = "Volume de contexto alto."
    elif sources or brief:
        depth = "medium"
        reason = "Ha material inicial suficiente para analise intermediaria."
    else:
        depth = "light"
        reason = "Pouco contexto; priorizar entrevista e perguntas."
    return {"level": depth, "reason": reason, "slug": slugify(f"{operation}-{depth}")}


def select_vendor_skills(operation: str) -> list[str]:
    skills = ["vendor/skills/ecc/product-capability"]
    if operation in {"create-web-app-design", "create-mobile-app-design", "facelift-existing-product", "recreate-legacy-design"}:
        skills.append("vendor/skills/ecc/frontend-patterns")
    if operation in {"generate-user-journey-diagram", "analyze-product-context"}:
        skills.append("vendor/skills/drawio-diagramming")
    if operation in {"create-design-system-foundation", "create-web-app-design", "create-mobile-app-design"}:
        skills.append("vendor/plugins/open-design/open-design")
    if operation in {"conduct-design-interview", "generate-dev-handoff"}:
        skills.append("vendor/skills/ecc/brand-voice")
    return skills


def render_documents(context: dict[str, Any]) -> dict[str, str]:
    operation = context["operation"]
    docs = {
        "design-brief.md": render_design_brief(context),
        "screen-inventory.md": render_screen_inventory(context),
        "figma-action-plan.md": render_figma_action_plan(context),
        "open-design-questions.md": render_open_questions(context),
        "source-traceability.md": render_traceability(context),
    }
    if operation in {"create-mobile-app-design", "create-web-app-design", "create-design-system-foundation", "facelift-existing-product", "recreate-legacy-design", "update-existing-figma-design"}:
        docs["design-system-spec.md"] = render_design_system_spec(context)
    if operation in {"create-mobile-app-design", "create-web-app-design"}:
        docs[f"{context['platform']}-screen-map.md"] = render_platform_screen_map(context)
    if operation in {"facelift-existing-product", "recreate-legacy-design", "capture-url-to-figma"}:
        docs["facelift-plan.md"] = render_facelift_plan(context)
    if operation in {"triage-design-feedback", "apply-design-feedback", "conduct-design-review-session"}:
        docs["feedback-triage.md"] = render_feedback_triage(context)
    if operation == "generate-user-journey-diagram":
        docs["journey-diagram.md"] = render_journey_diagram(context)
    if operation in {"generate-dev-handoff", "review-design-quality", "create-mobile-app-design", "create-web-app-design", "facelift-existing-product"}:
        docs["dev-handoff.md"] = render_dev_handoff(context)
        docs["design-quality-report.md"] = render_quality_report(context)
    if operation == "read-azure-card-for-design":
        docs["azure-card-design-context.md"] = render_azure_context(context)
    return docs


def render_design_brief(context: dict[str, Any]) -> str:
    sources = context["sources"]
    return f"""# {context['title']}

## Modo Do Agente

- Figma mode: `{context['figma_mode']['mode']}`
- Motivo: {context['figma_mode']['reason']}
- Profundidade: {context['depth']['level']} - {context['depth']['reason']}
- Plataforma: {context['platform']}
- Escopo: {context['scope']}

## Objetivo

Transformar o contexto recebido em direcao de design, telas, fluxos e handoff
para desenvolvimento. O agente deve perguntar quando uma decisao de negocio,
conteudo ou UX nao estiver sustentada pelas fontes.

## Contexto Fornecido

{quote(context['brief'] or summarize_sources(sources) or 'Nenhum brief textual informado. Priorizar entrevista e perguntas.')}

## Publico E Uso

- Publico alvo: {context['target_audience'] or 'A confirmar'}
- Estilo visual desejado: {context['design_style'] or 'A confirmar'}
- URL/app de referencia: {context['url'] or '-'}
- Arquivo Figma: {context['figma_file_url'] or '-'}
- Card Azure: {context['azure_card'] or '-'}

## Skills/Plugins Sugeridos

{bullet_list(context['vendor_skills'])}
"""


def render_screen_inventory(context: dict[str, Any]) -> str:
    screens = infer_screens(context)
    return f"""# Screen Inventory

## Telas / Areas Provaveis

{table(['Tela', 'Objetivo', 'Estados'], [[item, 'A definir com usuario e fontes', 'empty, loading, error, success, permission'] for item in screens])}

## Componentes Provaveis

{bullet_list(infer_components(context))}
"""


def render_figma_action_plan(context: dict[str, Any]) -> str:
    mode = context["figma_mode"]["mode"]
    execution = context.get("figma_execution")
    direct_steps = [
        "Carregar skill figma-use antes de qualquer escrita.",
        "Se novo arquivo for necessario, carregar figma-create-new-file e resolver planKey.",
        "Inspecionar arquivo existente com metadata/screenshot antes de alterar.",
        "Buscar libraries, componentes, variaveis e estilos com get_libraries/search_design_system.",
        "Criar ou atualizar frames incrementalmente com use_figma.",
        "Retornar node IDs criados/alterados e gerar handoff.",
    ]
    plan_steps = [
        "Usar este arquivo como roteiro para uma sessao com Figma MCP ativo.",
        "Criar arquivo Figma ou abrir o arquivo existente indicado.",
        "Criar paginas: Discovery, Design System, Flows, Screens, Review, Handoff.",
        "Aplicar screen inventory e design-system-spec.",
        "Validar com design-quality-report antes de aprovar.",
    ]
    execution_section = ""
    if execution:
        execution_section = f"""
## Execucao Real

- Status: `{execution.get('status', '-')}`
- Figma file: {execution.get('file_url') or execution.get('file_key') or '-'}
- Page: {execution.get('page_name') or '-'}
- Created node IDs: {', '.join(execution.get('created_node_ids') or []) or '-'}
- Mutated node IDs: {', '.join(execution.get('mutated_node_ids') or []) or '-'}
- Screenshots: {', '.join(execution.get('screenshot_refs') or []) or '-'}
"""
    return f"""# Figma Action Plan

## Modo

`{mode}`
{execution_section}

## Direct Mode Steps

{numbered_list(direct_steps)}

## Plan Only Steps

{numbered_list(plan_steps)}

## Arquivos/URLs

- Figma file: {context['figma_file_url'] or '-'}
- Figma project: {context['figma_project_url'] or '-'}
- URL/app/site: {context['url'] or '-'}
"""


def render_open_questions(context: dict[str, Any]) -> str:
    questions = [
        "Qual e o objetivo principal do usuario nesta experiencia?",
        "Quais personas precisam ser atendidas primeiro?",
        "Quais regras de negocio nao podem ser inferidas pelo design?",
        "Existe design system validado que deve ser usado?",
        "Quais estados de erro, vazio, carregamento e permissao sao obrigatorios?",
        "O design precisa seguir iOS, Material, web responsivo ou identidade propria?",
        "Quem aprova o design e qual criterio de aceite visual/funcional?",
    ]
    if context["operation"] in {"facelift-existing-product", "recreate-legacy-design"}:
        questions.extend(
            [
                "Quais partes do design antigo devem ser preservadas?",
                "O objetivo e facelift visual, redesign de UX ou recriacao fiel?",
                "Ha permissao para clonar/capturar a URL indicada?",
            ]
        )
    return "# Open Design Questions\n\n" + bullet_list(questions) + "\n"


def render_traceability(context: dict[str, Any]) -> str:
    rows = []
    if context["brief"]:
        rows.append(["BRIEF", "Brief informado", "design-brief.md"])
    for index, item in enumerate(context["sources"], start=1):
        rows.append([f"SRC-{index:03d}", item.path, item.warning or "lido/inventariado"])
    if not rows:
        rows.append(["SRC-000", "Sem fonte", "entrevista requerida"])
    return "# Source Traceability\n\n" + table(["ID", "Fonte", "Status"], rows) + "\n"


def render_design_system_spec(context: dict[str, Any]) -> str:
    return """# Design System Spec

## Foundations

- Color tokens: background, surface, border, text, muted, primary, danger, success.
- Typography: display, heading, title, body, caption.
- Spacing: 4, 8, 12, 16, 24, 32, 48.
- Radius: 4, 8, 12.

## Components

- Button: primary, secondary, destructive, ghost, disabled, loading.
- Input: default, focus, error, disabled, helper text.
- Card: data, action, summary.
- Navigation: web sidebar/topbar; mobile tabbar/header.
- Feedback: alert, toast, empty state, loading state.

## Figma Strategy

Reutilizar componentes e variaveis existentes antes de criar novos. Se nao
houver design system, criar foundations minimas em pagina separada.
"""


def render_platform_screen_map(context: dict[str, Any]) -> str:
    screens = infer_screens(context)
    return f"""# {context['platform'].title()} Screen Map

{table(['Frame', 'Breakpoint/Device', 'Conteudo', 'Estados'], [[screen, device_for(context['platform']), 'A definir a partir do brief', 'empty/loading/error/success/permission'] for screen in screens])}
"""


def render_facelift_plan(context: dict[str, Any]) -> str:
    return f"""# Facelift / Recreation Plan

## Tipo

- Operacao: {context['operation']}
- URL/projeto base: {context['url'] or context['figma_file_url'] or '-'}

## Processo

1. Capturar ou inventariar estado atual.
2. Identificar problemas de hierarquia, spacing, contraste, navegacao e conteudo.
3. Separar o que deve ser preservado do que pode mudar.
4. Criar pagina/frame `Current` e `Facelift v1`.
5. Aplicar design system e responsividade.
6. Gerar comparativo antes/depois e handoff.

## Guardrail

Nao clonar produto de terceiro para uso indevido. Use apenas material proprio,
autorizado ou como benchmark transformativo.
"""


def render_feedback_triage(context: dict[str, Any]) -> str:
    return f"""# Feedback Triage

## Feedback Recebido

{quote(context['feedback'] or 'Nenhum feedback informado.')}

## Classificacao

{table(['Tipo', 'Acao'], [
    ['Visual', 'Ajustar layout, hierarquia, cor, tipografia ou spacing.'],
    ['UX', 'Revisar fluxo, estados e decisao de interacao.'],
    ['Negocio', 'Perguntar antes de alterar regra ou comportamento.'],
    ['Handoff', 'Atualizar especificacao para desenvolvimento.'],
])}
"""


def render_journey_diagram(context: dict[str, Any]) -> str:
    return """# User Journey Diagram

```mermaid
flowchart LR
  A["Entrada do usuario"] --> B["Identifica objetivo"]
  B --> C{"Tem dados suficientes?"}
  C -- "Nao" --> D["Perguntar e coletar contexto"]
  C -- "Sim" --> E["Executar tarefa principal"]
  E --> F["Validar resultado"]
  F --> G["Concluir ou iterar"]
```
"""


def render_dev_handoff(context: dict[str, Any]) -> str:
    execution = context.get("figma_execution") or {}
    return f"""# Developer Handoff

## Escopo

- Plataforma: {context['platform']}
- Figma mode: {context['figma_mode']['mode']}
- Arquivo Figma: {execution.get('file_url') or context['figma_file_url'] or 'A definir'}
- Node IDs criados: {', '.join(execution.get('created_node_ids') or []) or '-'}
- Node IDs alterados: {', '.join(execution.get('mutated_node_ids') or []) or '-'}

## Entregaveis Esperados

- Frames principais.
- Estados obrigatorios.
- Componentes e tokens usados.
- Regras de interacao.
- Conteudo/microcopy.
- Perguntas abertas.

## Notas Para Desenvolvimento

- Nao implementar regras de negocio abertas sem confirmacao.
- Validar responsividade antes de iniciar front-end.
- Reusar componentes existentes do produto quando houver.
"""


def render_quality_report(context: dict[str, Any]) -> str:
    execution = context.get("figma_execution")
    checks = [
        ["Brief claro", "pass" if context["brief"] or context["sources"] else "needs_input"],
        ["Figma strategy definida", "pass"],
        ["Execucao Figma real", "pass" if execution else ("planned" if context["figma_mode"]["mode"] == "plan_only" else "needs_input")],
        ["Estados principais cobertos", "planned"],
        ["Design system considerado", "planned"],
        ["Acessibilidade basica", "planned"],
        ["Handoff gerado", "pass"],
    ]
    return "# Design Quality Report\n\n" + table(["Gate", "Status"], checks) + "\n"


def delegate_azure_read_card(card_id: str) -> dict[str, Any] | None:
    """Delegate card reading to azure-devops-orchestrator/read-card via CLI root.

    Returns parsed JSON output on success, None on failure (delegation unavailable).
    The caller must NOT interpret None as a successful read.
    """
    cli = ROOT / "ai-devkit"
    if not cli.exists():
        return None
    try:
        result = subprocess.run(
            [sys.executable, str(cli), "--json", "run", "azure-devops-orchestrator", "read-card", "--id", card_id],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        return None
    except Exception:  # noqa: BLE001
        return None


def render_azure_context(context: dict[str, Any]) -> str:
    card_id = context["azure_card"] or ""
    delegation_result = None
    delegation_status = "nao_tentada"

    if card_id:
        delegation_result = delegate_azure_read_card(card_id)
        delegation_status = "sucesso" if delegation_result else "falhou_modo_degradado"

    if delegation_result:
        card_data = json.dumps(delegation_result, ensure_ascii=False, indent=2)
        return f"""# Azure Card Design Context

- Card: {card_id}
- Delegated agent: azure-devops-orchestrator/read-card
- Status da delegacao: {delegation_status}
- Policy: leitura via CLI raiz; comentario/edicao no card somente com confirmacao explicita.

## Conteudo do Card (retornado pelo orchestrator)

```json
{card_data}
```
"""
    else:
        return f"""# Azure Card Design Context

- Card: {card_id or 'A informar'}
- Delegated agent: azure-devops-orchestrator/read-card
- Status da delegacao: {delegation_status}
- Policy: leitura via CLI raiz; comentario/edicao no card somente com confirmacao explicita.

## Modo Degradado

A delegacao ao azure-devops-orchestrator nao foi possivel (CLI indisponivel, agente nao encontrado
ou credenciais ausentes). O conteudo do card NAO foi lido automaticamente.

Para continuar, forneca o conteudo do card como arquivo (--source card.txt) ou texto colado no brief.

## Proximos Passos (quando conteudo for fornecido manualmente)

1. Extrair objetivo, criterios de aceite, anexos e comentarios relevantes.
2. Gerar design-brief.md a partir do conteudo.
3. Criar perguntas de UX/produto para lacunas.
"""


def infer_screens(context: dict[str, Any]) -> list[str]:
    text = " ".join([context["brief"], summarize_sources(context["sources"]), context["operation"]]).lower()
    candidates = ["Dashboard", "Listagem", "Detalhe", "Formulario", "Revisao", "Confirmacao"]
    if "login" in text or "auth" in text:
        candidates.insert(0, "Login")
    if "perfil" in text or "profile" in text:
        candidates.append("Perfil")
    if "config" in text or "settings" in text:
        candidates.append("Configuracoes")
    if context["operation"] in {"create-mobile-app-design", "create-web-app-design"}:
        candidates.append("Estado Vazio")
        candidates.append("Estado Erro")
    return list(dict.fromkeys(candidates))


def infer_components(context: dict[str, Any]) -> list[str]:
    base = ["Button", "Input", "Card", "Navigation", "Alert", "Empty State", "Loading", "Modal/Dialog"]
    if context["platform"] in {"web", "both"}:
        base.extend(["Sidebar", "Table", "Filter Bar"])
    if context["platform"] in {"mobile", "both"}:
        base.extend(["Mobile Header", "Tab Bar", "Bottom Sheet"])
    return list(dict.fromkeys(base))


def device_for(platform: str) -> str:
    if platform == "mobile":
        return "iPhone/Android"
    if platform == "web":
        return "Desktop 1440, tablet 768, mobile 390"
    return "Desktop e mobile"


def resolve_output_dir(value: str | None, operation: str, slug: str) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    return Path.cwd() / "docs" / "design" / slugify(operation)


def ensure_output_dir(output_dir: Path, yes_create_dir: bool) -> None:
    if output_dir.exists():
        if not output_dir.is_dir():
            raise ValueError(f"output path exists and is not a directory: {output_dir}")
        return
    if not yes_create_dir:
        print("Posso criar a pasta de artefatos de design neste projeto?")
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


def print_summary(output_dir: Path, documents: dict[str, str], figma_mode: dict[str, str]) -> None:
    print("# Figma UI/UX Product Designer")
    print("")
    print(f"Figma mode: {figma_mode['mode']}")
    print(f"Artefatos gerados em: {output_dir}")
    print("")
    for name in documents:
        print(f"- {output_dir / name}")


def summarize_sources(sources: list[SourceItem]) -> str:
    parts = []
    for item in sources[:12]:
        parts.append(f"Fonte: {item.path}\nTipo: {item.kind}\n{item.text[:1200]}")
        if item.warning:
            parts.append(f"Aviso: {item.warning}")
    return "\n\n".join(parts)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return slug or "design"


def quote(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return "-"
    return "\n".join(f"> {line}" if line.strip() else ">" for line in stripped.splitlines())


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- -"


def numbered_list(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        escaped = [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        lines.append("| " + " | ".join(escaped) + " |")
    return "\n".join(lines)
