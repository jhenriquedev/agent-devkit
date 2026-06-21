#!/usr/bin/env python3
"""Shared helpers for N2 Support Agent runners."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
CLI = ROOT / "ai-devkit"
DEFAULT_N2_TAG = "Analise N2"
DEFAULT_PATCH_FILE = "patch_plan.md"
CODE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".cs", ".java", ".go", ".sql"}


def load_fixture(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_output(content: str, output: str | None) -> None:
    if output:
        Path(output).write_text(content, encoding="utf-8")
    else:
        print(content)


def print_error(exc: Exception) -> int:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1


def run_ai_devkit(args: list[str]) -> str:
    process = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or f"ai-devkit failed: {' '.join(args)}")
    return process.stdout


def load_support_context(args: Any) -> dict[str, Any]:
    fixture = load_fixture(getattr(args, "fixture", None))
    work_item = fixture.get("work_item") or fixture.get("card")
    comments = fixture.get("comments") or {"comments": []}
    n1_contract = load_n1_contract(args, fixture)
    card_markdown = ""
    azure_loaded = False

    if work_item:
        azure_loaded = True
        card_markdown = render_fixture_card(work_item, comments)
    elif fixture and (getattr(args, "project", None) or getattr(args, "card", None)):
        azure_loaded = bool(getattr(args, "card", None))
        work_item = {
            "id": getattr(args, "card", None),
            "title": fixture.get("supportContext", {}).get("symptom") or "Fixture card",
            "state": "fixture",
            "description": "",
            "tags": [],
        }
        card_markdown = render_fixture_card(work_item, comments)
    elif getattr(args, "project", None) and getattr(args, "card", None):
        azure_loaded = True
        command = [
            "run",
            "azure-devops-orchestrator",
            "read-card",
            "--project",
            args.project,
            "--id",
            str(args.card),
            "--include-comments",
        ]
        card_markdown = run_ai_devkit(command)
        work_item = card_from_markdown(args.project, args.card, card_markdown)
    else:
        work_item = {}

    text = "\n".join(
        [
            card_markdown,
            json.dumps(fixture.get("supportContext") or {}, ensure_ascii=False),
            json.dumps(n1_contract or {}, ensure_ascii=False),
        ]
    )
    entities = extract_entities(text)
    return {
        "azureCardLoaded": azure_loaded,
        "n1ContractLoaded": bool(n1_contract),
        "codebasePath": str(getattr(args, "codebase_path", "") or ""),
        "card": card_summary(getattr(args, "project", None), getattr(args, "card", None), work_item),
        "cardMarkdown": card_markdown,
        "n1Contract": n1_contract,
        "fixtureSupportContext": fixture.get("supportContext") or {},
        "entities": entities,
        "symptom": infer_symptom(text, fixture.get("supportContext") or {}, work_item),
        "evidence": collect_evidence(fixture, n1_contract),
        "handoff": validate_handoff(n1_contract),
    }


def load_n1_contract(args: Any, fixture: dict[str, Any]) -> dict[str, Any] | None:
    if getattr(args, "n1_contract", None):
        return json.loads(Path(args.n1_contract).read_text(encoding="utf-8"))
    value = fixture.get("n1_contract") or fixture.get("n1Contract")
    return value if isinstance(value, dict) else None


def analyze_codebase(codebase_path: str | None, context: dict[str, Any]) -> dict[str, Any]:
    if not codebase_path:
        return {
            "filesInspected": [],
            "relevantMethods": [],
            "businessRulesFound": [],
            "technicalFindings": [],
            "status": "skipped",
            "reason": "codebase_path was not provided",
        }
    root = Path(codebase_path).expanduser()
    if not root.exists():
        return {
            "filesInspected": [],
            "relevantMethods": [],
            "businessRulesFound": [],
            "technicalFindings": [],
            "status": "unavailable",
            "reason": f"codebase_path does not exist: {root}",
        }

    tokens = relevant_tokens(context)
    candidates = []
    methods = []
    for path in iter_code_files(root):
        rel = str(path.relative_to(root))
        text = path.read_text(encoding="utf-8", errors="ignore")
        score = score_text(text, tokens) + score_text(rel, tokens)
        if score <= 0:
            continue
        candidates.append(
            {
                "file": rel,
                "score": score,
                "fileKind": file_kind(rel),
                "matchedTerms": sorted(
                    {
                        token
                        for token in tokens
                        if token and (token.lower() in text.lower() or token.lower() in rel.lower())
                    }
                )[:8],
                "summary": summarize_code_file(text),
            }
        )
        methods.extend(extract_methods(rel, text))
    findings = sorted(candidates, key=finding_sort_key)[:12]
    files = [item["file"] for item in findings]

    return {
        "filesInspected": files,
        "relevantMethods": methods[:20],
        "businessRulesFound": [item["summary"] for item in findings if item["summary"]],
        "technicalFindings": findings,
        "status": "completed" if files else "no_direct_match",
        "reason": "Relevant code files found" if files else "No code file matched the support context tokens",
    }


def classify_root_cause(context: dict[str, Any], code_analysis: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(
        [
            context.get("symptom") or "",
            json.dumps(context.get("n1Contract") or {}, ensure_ascii=False),
            json.dumps(context.get("evidence") or [], ensure_ascii=False),
            json.dumps(code_analysis.get("technicalFindings") or [], ensure_ascii=False),
        ]
    ).lower()
    if code_analysis.get("filesInspected") and any(term in text for term in ("exception", "erro", "bug", "backend", "handler", "service", "job")):
        category = "backend_bug"
        confidence = 0.78
    elif any(term in text for term in ("pendente", "pending", "documento", "document")):
        category = "external_provider_issue" if "bpo" in text else "customer_pending_action"
        confidence = 0.72
    elif any(term in text for term in ("inconsisten", "diverg", "status")):
        category = "data_inconsistency"
        confidence = 0.74
    elif not code_analysis.get("filesInspected"):
        category = "insufficient_evidence"
        confidence = 0.52
    else:
        category = "backend_bug"
        confidence = 0.68
    return {
        "category": category,
        "confidence": confidence,
        "summary": root_cause_summary(category, context, code_analysis),
        "evidence": root_cause_evidence(context, code_analysis),
        "contradictions": find_contradictions(context),
        "missingEvidence": missing_evidence(context, code_analysis),
    }


def build_patch_plan_contract(
    *,
    context: dict[str, Any],
    code_analysis: dict[str, Any],
    root_cause: dict[str, Any],
    output: str | None,
    project: str | None,
    card: int | None,
    execute: bool,
) -> dict[str, Any]:
    blocking = blocking_questions(context, code_analysis, root_cause, output, project, card)
    has_destination = bool(output or (project and card))
    ready = not blocking and has_destination
    delivery = "local_path" if output else "azure_attachment" if project and card else "missing_destination"
    return {
        "generated": True,
        "readyForImplementation": ready,
        "deliveryMode": delivery,
        "path": str(Path(output).expanduser()) if output else None,
        "fileName": DEFAULT_PATCH_FILE,
        "azureAttachment": {
            "project": project,
            "card": card,
            "fileName": DEFAULT_PATCH_FILE,
            "attached": bool(execute and project and card and not output),
            "requiresExecute": bool(project and card and not execute),
        } if project and card else None,
        "blockingQuestions": blocking,
    }


def render_patch_plan(
    *,
    context: dict[str, Any],
    code_analysis: dict[str, Any],
    root_cause: dict[str, Any],
    patch_plan: dict[str, Any],
) -> str:
    card = context.get("card") or {}
    entities = context.get("entities") or {}
    files = code_analysis.get("filesInspected") or ["src/<arquivo-afetado>"]
    primary_file = files[0]
    test_file = infer_test_file(primary_file)
    questions = patch_plan.get("blockingQuestions") or []
    lines = [
        f"# Patch Plan - Card {card.get('id') or '-'}",
        "",
        "## 1. Contexto",
        "",
        f"- Projeto Azure: {card.get('project') or '-'}",
        f"- Card: {card.get('id') or '-'}",
        f"- Sintoma: {context.get('symptom') or '-'}",
        f"- Cliente/CPF mascarado: {entities.get('cpfMasked') or '-'}",
        f"- Proposta/contrato: {entities.get('proposalNumber') or entities.get('contractNumber') or '-'}",
        f"- Origem da analise: {'contrato N1' if context.get('n1ContractLoaded') else 'card/fixture N2'}",
        "",
        "## 2. Diagnostico",
        "",
        "### Causa provavel",
        "",
        f"- Categoria: `{root_cause.get('category')}`",
        f"- Confianca: {root_cause.get('confidence')}",
        f"- Resumo: {root_cause.get('summary')}",
        "",
        "### Evidencias que sustentam a causa",
        "",
        *bullet_lines(root_cause.get("evidence") or ["Sem evidencia objetiva suficiente."]),
        "",
        "### Evidencias contraditorias",
        "",
        *bullet_lines(root_cause.get("contradictions") or ["Nenhuma contradicao identificada."]),
        "",
        "### Lacunas conhecidas",
        "",
        *bullet_lines(root_cause.get("missingEvidence") or ["Nenhuma lacuna critica identificada."]),
        "",
        "## 3. Perguntas em aberto",
        "",
        *checkbox_lines(questions or ["Nenhuma pergunta bloqueante identificada."]),
        "",
        "## 4. Escopo do patch",
        "",
        "### Dentro do escopo",
        "",
        "- Reproduzir o problema com teste automatizado.",
        "- Corrigir o fluxo identificado pela analise N2.",
        "- Validar regressao com testes existentes.",
        "",
        "### Fora do escopo",
        "",
        "- Alterar dados de producao sem agente operador e aprovacao explicita.",
        "- Implementar refatoracoes nao relacionadas ao sintoma do card.",
        "",
        "## 5. Estrategia segura de desenvolvimento",
        "",
        "1. Criar teste que reproduz o problema.",
        "2. Executar o teste e confirmar falha pelo motivo esperado.",
        "3. Implementar a menor alteracao no codigo afetado.",
        "4. Rodar teste focado e suite relacionada.",
        "5. Avaliar necessidade de migration ou script operacional.",
        "6. Registrar evidencias no card.",
        "",
        "## 6. Atividades",
        "",
        "### Atividade 1 - Reproduzir o problema com teste",
        "",
        "Arquivos criados/alterados:",
        f"- `{test_file}`",
        "",
        "Objetivo: criar um teste vermelho que represente o sintoma do card.",
        "",
        "Passos:",
        "- Montar fixture com o estado observado pelo N1/N2.",
        "- Chamar o metodo/handler relacionado ao fluxo afetado.",
        "- Assertar o comportamento esperado.",
        "",
        "Criterios de aceite:",
        "- O teste falha antes do patch.",
        "- A falha aponta para o comportamento incorreto, nao para erro de setup.",
        "",
        "### Atividade 2 - Corrigir regra/codigo",
        "",
        "Arquivos criados/alterados:",
        *[f"- `{item}`" for item in files],
        "",
        "Objetivo: corrigir a causa raiz com alteracao pequena e rastreavel.",
        "",
        "Passos:",
        "- Aplicar a regra faltante ou corrigir o fluxo identificado.",
        "- Preservar contratos publicos quando possivel.",
        "- Evitar refatoracao ampla fora do sintoma.",
        "",
        "Criterios de aceite:",
        "- O teste novo passa.",
        "- Testes existentes relacionados continuam passando.",
        "",
        "### Atividade 3 - Migration, se necessario",
        "",
        "Arquivos criados/alterados:",
        "- `migrations/<timestamp>_<descricao>.sql` se houver mudanca de schema ou backfill.",
        "",
        "Objetivo: aplicar ajuste de dados/schema apenas se a causa raiz exigir.",
        "",
        "Rollback:",
        "- Criar script inverso ou validacao de idempotencia antes de executar em producao.",
        "",
        "Criterios de aceite:",
        "- Migration e idempotente ou possui rollback claro.",
        "- Validacao read-only confirma o resultado esperado.",
        "",
        "### Atividade 4 - Observabilidade/logs, se necessario",
        "",
        "Arquivos criados/alterados:",
        f"- `{primary_file}`",
        "",
        "Objetivo: garantir log suficiente para diagnosticar reincidencia.",
        "",
        "Criterios de aceite:",
        "- Logs nao imprimem CPF cru, segredo ou payload sensivel.",
        "- Logs incluem correlation id/request id quando disponivel.",
        "",
        "## Plano TDD",
        "",
        "### Teste vermelho esperado",
        "",
        f"- Criar teste em `{test_file}` reproduzindo: {context.get('symptom') or 'sintoma do card'}.",
        "",
        "### Implementacao minima",
        "",
        f"- Alterar `{primary_file}` somente no ponto necessario para passar o teste.",
        "",
        "### Refatoracao segura",
        "",
        "- Extrair helper apenas se reduzir duplicacao real ou deixar a regra testavel.",
        "",
        "### Testes de regressao",
        "",
        "- Rodar teste focado.",
        "- Rodar suite do modulo afetado.",
        "",
        "## 8. Comandos de validacao",
        "",
        "```bash",
        "# ajuste conforme stack do projeto analisado",
        "python3 -m pytest",
        "python3 -m unittest",
        "```",
        "",
        "## Criterios de aceite finais",
        "",
        "- [ ] O problema original foi reproduzido por teste.",
        "- [ ] O teste falha antes do patch.",
        "- [ ] O teste passa depois do patch.",
        "- [ ] Nao houve regressao nos testes existentes.",
        "- [ ] Migration validada, se existir.",
        "- [ ] Logs/observabilidade suficientes, se aplicavel.",
        "- [ ] Comentario tecnico gerado para o card.",
        "",
        "## 10. Riscos",
        "",
        "- Alteracao pode afetar fluxo de onboarding/proposta similar.",
        "- Dados antigos podem exigir correcao operacional separada.",
        "",
        "## 11. Plano de rollback",
        "",
        "- Reverter patch de codigo.",
        "- Reverter migration/backfill com script documentado, se houver.",
        "- Reprocessar apenas registros impactados apos validacao.",
        "",
        "## 12. Comentario sugerido para Azure DevOps",
        "",
        render_card_comment(root_cause, patch_plan),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_contract(args: Any, *, write_patch_plan: bool = True) -> tuple[dict[str, Any], str]:
    context = load_support_context(args)
    code_analysis = analyze_codebase(getattr(args, "codebase_path", None), context)
    root_cause = classify_root_cause(context, code_analysis)
    patch_output = getattr(args, "output", None) if write_patch_plan else None
    patch_plan = build_patch_plan_contract(
        context=context,
        code_analysis=code_analysis,
        root_cause=root_cause,
        output=patch_output,
        project=getattr(args, "project", None),
        card=getattr(args, "card", None),
        execute=bool(getattr(args, "execute", False)),
    )
    markdown = render_patch_plan(
        context=context,
        code_analysis=code_analysis,
        root_cause=root_cause,
        patch_plan=patch_plan,
    )
    output_path_for_attachment = None
    temporary_patch_path = None
    if patch_output:
        output_path = Path(patch_output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        output_path_for_attachment = str(output_path)
    elif getattr(args, "project", None) and getattr(args, "card", None) and getattr(args, "execute", False):
        temporary = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=f"-{DEFAULT_PATCH_FILE}", delete=False)
        temporary.write(markdown)
        temporary.close()
        temporary_patch_path = temporary.name
        output_path_for_attachment = temporary_patch_path
    azure_actions = build_azure_actions(args, patch_plan, root_cause, markdown, output_path_for_attachment)
    if temporary_patch_path:
        Path(temporary_patch_path).unlink(missing_ok=True)
    contract = {
        "runbook": "n2-root-cause-investigation",
        "version": "0.1.0",
        "input": {
            "project": getattr(args, "project", None),
            "card": getattr(args, "card", None),
            "codebasePath": getattr(args, "codebase_path", None),
            "execute": bool(getattr(args, "execute", False)),
        },
        "supportContext": {
            key: value
            for key, value in context.items()
            if key not in {"cardMarkdown", "n1Contract"}
        },
        "codeAnalysis": code_analysis,
        "runtimeCorrelation": correlate_runtime(context, code_analysis),
        "rootCause": root_cause,
        "resolutionPlan": build_resolution_plan(root_cause, patch_plan),
        "patchPlan": patch_plan,
        "azureActions": azure_actions,
        "artifacts": {
            "azureInternalComment": render_card_comment(root_cause, patch_plan),
            "patchPlanPreview": markdown[:1200],
        },
        "audit": {
            "executedAt": datetime.now(timezone.utc).isoformat(),
            "orchestratedAgents": sorted({item["agent"] for item in azure_actions}),
            "dataSources": ["azure-devops"] if context.get("azureCardLoaded") else [],
        },
    }
    return contract, markdown


def build_azure_actions(
    args: Any,
    patch_plan: dict[str, Any],
    root_cause: dict[str, Any],
    markdown: str,
    attachment_path: str | None,
) -> list[dict[str, Any]]:
    project = getattr(args, "project", None)
    card = getattr(args, "card", None)
    if not (project and card):
        return []
    execute = bool(getattr(args, "execute", False))
    action_specs = [
        (
            "add-n2-tag",
            "update-card-tags",
            [
                "--project",
                project,
                "--id",
                str(card),
                "--add-tag",
                DEFAULT_N2_TAG,
                "--reason",
                "N2 analysis started",
            ],
            f"Add tag {DEFAULT_N2_TAG}",
        ),
        (
            "comment-card",
            "comment-card",
            [
                "--project",
                project,
                "--id",
                str(card),
                "--comment",
                render_card_comment(root_cause, patch_plan),
            ],
            render_card_comment(root_cause, patch_plan),
        ),
    ]
    if attachment_path:
        action_specs.append(
            (
                "attach-patch-plan",
                "attach-file",
                [
                    "--project",
                    project,
                    "--id",
                    str(card),
                    "--file",
                    attachment_path,
                    "--comment",
                    "N2 patch_plan.md",
                ],
                f"Attach {patch_plan.get('fileName') or DEFAULT_PATCH_FILE} to card {card}",
            )
        )
    else:
        action_specs.append(
            (
                "attach-patch-plan",
                "attach-file",
                [],
                f"Attach {patch_plan.get('fileName') or DEFAULT_PATCH_FILE} to card {card}",
            )
        )

    actions = []
    for action_id, capability, command_args, summary in action_specs:
        action = {
            "id": action_id,
            "agent": "azure-devops-orchestrator",
            "capability": capability,
            "mode": "executed" if execute else "dry_run",
            "status": "planned" if not execute else "completed",
            "summary": summary,
        }
        if execute and command_args:
            command = ["run", "azure-devops-orchestrator", capability, *command_args, "--execute"]
            if getattr(args, "fixture", None):
                command.extend(["--fixture", args.fixture])
            try:
                action["outputPreview"] = run_ai_devkit(command)[:800]
            except Exception as exc:
                action["status"] = "failed"
                action["error"] = value_or_dash(exc)
        actions.append(action)
    return actions


def render_contract_markdown(contract: dict[str, Any]) -> str:
    lines = [
        "# N2 Investigation",
        "",
        f"- Root cause: {contract['rootCause']['category']}",
        f"- Confidence: {contract['rootCause']['confidence']}",
        f"- Patch plan: {contract['patchPlan'].get('path') or contract['patchPlan'].get('deliveryMode')}",
        "",
        "## Contract",
        "",
        "```json",
        json.dumps(contract, ensure_ascii=False, indent=2),
        "```",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_fixture_card(work_item: dict[str, Any], comments: Any) -> str:
    comments_list = (comments or {}).get("comments", []) if isinstance(comments, dict) else comments or []
    lines = [
        "# Card Analysis",
        "",
        f"- ID: {value_or_dash(work_item.get('id'))}",
        f"- Title: {value_or_dash(work_item.get('title'))}",
        f"- State: {value_or_dash(work_item.get('state'))}",
        f"- Current column: {value_or_dash(work_item.get('board_column'))}",
        f"- Tags: {', '.join(work_item.get('tags') or []) or '-'}",
        f"- Description: {value_or_dash(work_item.get('description'))}",
        "",
        "## Comments",
    ]
    lines.extend(f"- {value_or_dash(item.get('text'))}" for item in comments_list) if comments_list else lines.append("- No comments loaded.")
    return "\n".join(lines).rstrip() + "\n"


def card_from_markdown(project: str, card_id: int, markdown: str) -> dict[str, Any]:
    return {
        "id": card_id,
        "project": project,
        "title": parse_field(markdown, "Title"),
        "state": parse_field(markdown, "State"),
        "board_column": parse_field(markdown, "Current column"),
        "description": markdown,
    }


def parse_field(markdown: str, label: str) -> str | None:
    match = re.search(rf"^- {re.escape(label)}:\s*(.+)$", markdown, re.M)
    return match.group(1).strip() if match else None


def card_summary(project: str | None, card_id: int | None, work_item: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": project,
        "id": work_item.get("id") or card_id,
        "title": work_item.get("title"),
        "state": work_item.get("state"),
        "column": work_item.get("board_column"),
        "tags": work_item.get("tags") or [],
    }


def extract_entities(text: str) -> dict[str, Any]:
    cpf = first_match(text, r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
    proposal = first_match(text, r"(?i)\b(?:proposta|proposal)\D{0,20}(\d{4,})\b")
    contract = first_match(text, r"(?i)\b(?:contrato|contract)\D{0,20}([A-Za-z0-9-]{4,})\b")
    return {
        "cpfMasked": mask_cpf(cpf) if cpf else None,
        "cpfPresent": bool(cpf),
        "proposalNumber": proposal,
        "contractNumber": contract,
    }


def first_match(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    if not match:
        return None
    return match.group(1) if match.lastindex else match.group(0)


def mask_cpf(value: str) -> str:
    if "***" in str(value or ""):
        return str(value)
    digits = re.sub(r"\D", "", value)
    if len(digits) != 11:
        return "***"
    return f"{digits[:3]}.***.***-{digits[-2:]}"


def infer_symptom(text: str, support_context: dict[str, Any] | None = None, work_item: dict[str, Any] | None = None) -> str:
    support_context = support_context or {}
    work_item = work_item or {}
    preferred = support_context.get("symptom") or " ".join(
        str(item or "")
        for item in (
            work_item.get("title"),
            work_item.get("description"),
        )
    )
    cleaned = value_or_dash(sanitize_text(preferred or text))
    return cleaned[:260] if cleaned != "-" else "Sintoma nao informado."


def collect_evidence(fixture: dict[str, Any], n1_contract: dict[str, Any] | None) -> list[str]:
    evidence = []
    support = fixture.get("supportContext") or {}
    evidence.extend(sanitize_text(str(item)) for item in support.get("evidence") or [])
    for check in (n1_contract or {}).get("checks") or []:
        evidence.append(sanitize_text(f"{check.get('id')}: {check.get('status')} {check.get('reason') or ''}".strip()))
    return evidence


def validate_handoff(n1_contract: dict[str, Any] | None) -> dict[str, Any]:
    if not n1_contract:
        return {"accepted": False, "missingRequiredEvidence": ["n1_contract"]}
    missing = [key for key in ("entities", "checks", "decision") if key not in n1_contract]
    return {"accepted": not missing, "missingRequiredEvidence": missing}


def iter_code_files(root: Path) -> list[Path]:
    ignored = {".git", "node_modules", "dist", "build", "__pycache__", ".venv", "venv"}
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        if any(part in ignored for part in path.parts):
            continue
        files.append(path)
        if len(files) >= 500:
            break
    return files


def relevant_tokens(context: dict[str, Any]) -> list[str]:
    text = " ".join(
        [
            context.get("symptom") or "",
            json.dumps(context.get("evidence") or [], ensure_ascii=False),
            json.dumps(context.get("fixtureSupportContext") or {}, ensure_ascii=False),
        ]
    ).lower()
    candidates = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{3,}", text)
    preferred = ["onboarding", "proposal", "proposta", "document", "documento", "bpo", "card", "service", "handler", "job"]
    return list(dict.fromkeys([*preferred, *candidates]))[:60]


def score_text(text: str, tokens: list[str]) -> int:
    lowered = text.lower()
    return sum(1 for token in tokens if token and token.lower() in lowered)


def summarize_code_file(text: str) -> str:
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith(("def ", "class ", "function ", "public ", "private ", "async ")):
            return line[:180]
    return "Arquivo contem termos relacionados ao contexto N2."


def extract_methods(rel: str, text: str) -> list[dict[str, str]]:
    methods = []
    for index, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if re.match(r"(def|class|function|async function)\s+", line) or re.match(r"(public|private|protected)\s+.*\(", line):
            methods.append({"file": rel, "line": index, "signature": line[:180]})
    return methods


def root_cause_summary(category: str, context: dict[str, Any], code_analysis: dict[str, Any]) -> str:
    files = ", ".join(code_analysis.get("filesInspected") or [])
    if category == "backend_bug":
        return f"Codigo relacionado foi localizado e deve ser validado com teste antes do patch. Arquivos candidatos: {files or '-'}."
    if category == "external_provider_issue":
        return "Evidencias indicam pendencia ou falha em sistema externo, exigindo confirmar contrato e tratamento local."
    if category == "data_inconsistency":
        return "Evidencias indicam divergencia de estado entre sistemas ou persistencia."
    return "Evidencia ainda insuficiente para causa raiz segura."


def root_cause_evidence(context: dict[str, Any], code_analysis: dict[str, Any]) -> list[str]:
    evidence = [sanitize_text(item) for item in context.get("evidence") or []]
    for item in code_analysis.get("technicalFindings") or []:
        evidence.append(sanitize_text(f"Codigo candidato: {item.get('file')} ({item.get('summary')})"))
    return evidence[:12]


def find_contradictions(context: dict[str, Any]) -> list[str]:
    checks = (context.get("n1Contract") or {}).get("checks") or []
    statuses = {item.get("id"): item.get("status") for item in checks}
    if statuses.get("bpo-proposal") == "pending" and statuses.get("proposal-status") == "completed":
        return ["BPO indica pendencia enquanto proposta interna aparece concluida."]
    return []


def missing_evidence(context: dict[str, Any], code_analysis: dict[str, Any]) -> list[str]:
    missing = []
    if not context.get("n1ContractLoaded"):
        missing.append("Contrato N1 nao foi informado; diagnostico usa apenas contexto N2/card.")
    if not code_analysis.get("filesInspected"):
        missing.append("Nenhum arquivo de codigo relacionado foi localizado.")
    return missing


def blocking_questions(
    context: dict[str, Any],
    code_analysis: dict[str, Any],
    root_cause: dict[str, Any],
    output: str | None,
    project: str | None,
    card: int | None,
) -> list[str]:
    questions = []
    if not output and not (project and card):
        questions.append("Informe --output /path/patch_plan.md ou --project + --card para entregar o patch_plan.md.")
    if root_cause.get("category") == "insufficient_evidence":
        questions.append("Qual fluxo/arquivo/projeto deve ser analisado para confirmar a causa raiz?")
    if code_analysis.get("status") == "unavailable":
        questions.append(code_analysis.get("reason") or "codebase_path indisponivel.")
    return questions


def correlate_runtime(context: dict[str, Any], code_analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "confirmedEvidence": root_cause_evidence(context, code_analysis),
        "contradictions": find_contradictions(context),
        "missingEvidence": missing_evidence(context, code_analysis),
    }


def build_resolution_plan(root_cause: dict[str, Any], patch_plan: dict[str, Any]) -> dict[str, Any]:
    category = root_cause.get("category")
    if category in {"backend_bug", "data_inconsistency"}:
        path = "patch_plan_required"
    elif category == "external_provider_issue":
        path = "specialist_or_external_followup"
    else:
        path = "collect_more_evidence"
    return {
        "path": path,
        "requiresMutation": category in {"data_inconsistency"},
        "recommendedAgent": "database-change-operator" if category == "data_inconsistency" else None,
        "steps": [
            "Revisar patch_plan.md.",
            "Executar TDD conforme plano.",
            "Atualizar card com evidencias da validacao.",
        ] if patch_plan.get("readyForImplementation") else ["Responder perguntas bloqueantes antes de implementar."],
    }


def render_card_comment(root_cause: dict[str, Any], patch_plan: dict[str, Any]) -> str:
    return (
        f"Analise N2: causa provavel `{root_cause.get('category')}` "
        f"(confianca {root_cause.get('confidence')}). "
        f"Patch plan: {patch_plan.get('path') or patch_plan.get('deliveryMode')}. "
        f"Resumo: {root_cause.get('summary')}"
    )


def infer_test_file(source_file: str) -> str:
    path = Path(source_file)
    if "test" in path.name.lower():
        return source_file
    return str(Path("tests") / f"test_{path.stem}.py")


def bullet_lines(values: list[str]) -> list[str]:
    return [f"- {value}" for value in values]


def checkbox_lines(values: list[str]) -> list[str]:
    return [f"- [ ] {value}" for value in values]


def value_or_dash(value: Any) -> str:
    if value is None:
        return "-"
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split()) or "-"


def sanitize_text(value: Any) -> str:
    text = value_or_dash(value)
    text = re.sub(
        r"\b(\d{3})[.\-\s]?(\d{3})[.\-\s]?(\d{3})[.\-\s]?(\d{2})\b",
        lambda match: f"{match.group(1)}.***.***-{match.group(4)}",
        text,
    )
    return re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[email-redacted]", text)


def file_kind(path: str) -> str:
    lowered = path.lower()
    normalized = f"/{lowered}"
    if "/tests/" in normalized or "/test/" in normalized or lowered.startswith("test_") or lowered.endswith((".test.ts", ".spec.ts", ".test.js", ".spec.js")):
        return "test"
    if "migration" in lowered or lowered.endswith(".sql"):
        return "migration"
    if lowered.endswith((".md", ".json", ".yaml", ".yml")):
        return "support"
    return "source"


def finding_sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
    priority = {"source": 0, "migration": 1, "test": 2, "support": 3}
    return (priority.get(item.get("fileKind"), 9), -int(item.get("score") or 0), item.get("file") or "")


def validate_handoff_payload(context: dict[str, Any]) -> dict[str, Any]:
    handoff = context.get("handoff") or {}
    missing = handoff.get("missingRequiredEvidence") or []
    return {
        "accepted": bool(handoff.get("accepted")),
        "missingRequiredEvidence": missing,
        "n1ContractLoaded": bool(context.get("n1ContractLoaded")),
        "entities": context.get("entities") or {},
        "needsN1Rerun": bool(missing),
    }


def select_specialist_checks(context: dict[str, Any], root_cause: dict[str, Any]) -> dict[str, Any]:
    text = " ".join([context.get("symptom") or "", json.dumps(context.get("evidence") or [], ensure_ascii=False)]).lower()
    selected = []
    if "bpo" in text or "proposta" in text or "proposal" in text:
        selected.append({"agent": "bpo-analyser", "capability": "analyze-proposal", "reason": "Validar proposta/documentos BPO."})
    if "log" in text or "erro" in text or root_cause.get("category") in {"backend_bug", "integration_failure"}:
        selected.append({"agent": "elasticsearch-log-analyzer", "capability": "search-log-events", "reason": "Validar erro runtime no periodo do chamado."})
    if root_cause.get("category") in {"data_inconsistency", "backend_bug"}:
        selected.append({"agent": "postgres-data-analyzer", "capability": "run-readonly-query", "reason": "Validar estado persistido relacionado ao fluxo."})
    if not selected:
        selected.append({"agent": "n1-support-agent", "capability": "execute-n1-card-runbook", "reason": "Handoff insuficiente para especializacao N2."})
    return {"selectedChecks": selected}


def execute_specialist_validation_payload(context: dict[str, Any], root_cause: dict[str, Any]) -> dict[str, Any]:
    validations = []
    for check in select_specialist_checks(context, root_cause)["selectedChecks"]:
        validations.append(
            {
                **check,
                "status": "planned",
                "resultSummary": "Validacao especialista planejada; execucao real deve usar agente indicado com parametros do contrato N2.",
            }
        )
    return {"validations": validations}


def rank_code_findings_payload(code_analysis: dict[str, Any]) -> dict[str, Any]:
    ranked = []
    for index, item in enumerate(sorted(code_analysis.get("technicalFindings") or [], key=finding_sort_key), start=1):
        ranked.append({**item, "rank": index})
    return {"rankedFindings": ranked}


def build_reproduction_strategy_payload(context: dict[str, Any], code_analysis: dict[str, Any]) -> dict[str, Any]:
    files = code_analysis.get("filesInspected") or ["src/<arquivo-afetado>"]
    primary = files[0]
    return {
        "testPlan": {
            "testFile": infer_test_file(primary),
            "targetFile": primary,
            "given": context.get("evidence") or ["Estado observado no card/N1"],
            "when": context.get("symptom") or "Executar fluxo afetado",
            "then": "O comportamento esperado deve ser assertado antes do patch.",
            "redGreenRefactor": ["Criar teste vermelho", "Aplicar menor patch", "Refatorar mantendo suite verde"],
        }
    }


def review_patch_plan_readiness_payload(patch_plan: dict[str, Any], root_cause: dict[str, Any], code_analysis: dict[str, Any]) -> dict[str, Any]:
    blockers = list(patch_plan.get("blockingQuestions") or [])
    if not code_analysis.get("filesInspected"):
        blockers.append("Nenhum arquivo de codigo foi selecionado para patch.")
    if root_cause.get("confidence", 0) < 0.65:
        blockers.append("Confianca da causa raiz abaixo do minimo recomendado para implementacao.")
    return {
        "readyForImplementation": bool(patch_plan.get("readyForImplementation")) and not blockers,
        "blockers": blockers,
        "rootCauseCategory": root_cause.get("category"),
        "confidence": root_cause.get("confidence"),
    }
