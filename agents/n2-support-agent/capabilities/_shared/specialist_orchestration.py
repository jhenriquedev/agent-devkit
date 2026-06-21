#!/usr/bin/env python3
"""Specialist validation orchestration for the N2 Support Agent."""

from __future__ import annotations

from typing import Any, Callable


RunCommand = Callable[[list[str]], str]


def execute_specialist_validations(
    *,
    context: dict[str, Any],
    selected_checks: list[dict[str, Any]],
    execute: bool,
    fixture: str | None,
    run_command: RunCommand,
) -> dict[str, Any]:
    validations = []
    for check in selected_checks:
        command = build_specialist_command(check, context)
        validation = {
            **check,
            "status": "planned",
            "commandPreview": render_command(command) if command else None,
            "resultSummary": "Validacao especialista planejada.",
        }
        if not command:
            validation["status"] = "skipped"
            validation["resultSummary"] = "Sem contrato executavel seguro para esta validacao nesta rodada."
        elif execute:
            command_to_run = list(command)
            if fixture and supports_fixture(command_to_run):
                command_to_run.extend(["--fixture", fixture])
            try:
                output = run_command(command_to_run)
                validation["status"] = "executed"
                validation["resultSummary"] = summarize_output(output)
            except Exception as exc:
                validation["status"] = "failed"
                validation["resultSummary"] = compact_text(str(exc))[:500]
        validations.append(validation)
    return {"validations": validations}


def build_specialist_command(check: dict[str, Any], context: dict[str, Any]) -> list[str]:
    agent = check.get("agent")
    capability = check.get("capability")
    entities = context.get("entities") or {}
    n1_entities = ((context.get("n1Contract") or {}).get("entities") or {})
    proposal = entities.get("proposalNumber") or n1_entities.get("proposalNumber")
    cpf_masked = entities.get("cpfMasked") or n1_entities.get("cpfMasked")

    if agent == "bpo-analyser" and capability == "analyze-proposal" and proposal:
        return ["run", "bpo-analyser", "analyze-proposal", "--proposal-number", str(proposal), "--format", "json"]
    if agent == "bpo-analyser" and capability == "find-latest-proposal-by-cpf" and cpf_masked and "***" not in str(cpf_masked):
        return ["run", "bpo-analyser", "find-latest-proposal-by-cpf", "--cpf", str(cpf_masked), "--format", "json"]
    return []


def supports_fixture(command: list[str]) -> bool:
    if len(command) < 3:
        return False
    return command[1] in {"bpo-analyser"}


def render_command(command: list[str]) -> str | None:
    if not command:
        return None
    return "./ai-devkit " + " ".join(command)


def summarize_output(output: str) -> str:
    text = compact_text(output)
    if not text:
        return "Validacao executada sem conteudo de saida."
    return text[:700]


def compact_text(value: Any) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())
