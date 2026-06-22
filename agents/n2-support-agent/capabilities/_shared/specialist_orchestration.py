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
        command, missing_inputs, skip_reason = build_specialist_command(check, context)
        validation = {
            **check,
            "status": "planned",
            "commandPreview": render_command(command) if command else None,
            "resultSummary": "Validacao especialista planejada.",
        }
        if not command:
            validation["status"] = "skipped"
            validation["missingInputs"] = missing_inputs
            validation["resultSummary"] = skip_reason or "Sem contrato executavel seguro para esta validacao nesta rodada."
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


def build_specialist_command(check: dict[str, Any], context: dict[str, Any]) -> tuple[list[str], list[str], str | None]:
    agent = check.get("agent")
    capability = check.get("capability")
    entities = context.get("entities") or {}
    n1_entities = ((context.get("n1Contract") or {}).get("entities") or {})
    proposal = entities.get("proposalNumber") or n1_entities.get("proposalNumber")
    cpf_masked = entities.get("cpfMasked") or n1_entities.get("cpfMasked")
    params = specialist_params(context)

    if agent == "bpo-analyser" and capability == "analyze-proposal" and proposal:
        return ["run", "bpo-analyser", "analyze-proposal", "--proposal-number", str(proposal), "--format", "json"], [], None
    if agent == "bpo-analyser" and capability == "find-latest-proposal-by-cpf" and cpf_masked and "***" not in str(cpf_masked):
        return ["run", "bpo-analyser", "find-latest-proposal-by-cpf", "--cpf", str(cpf_masked), "--format", "json"], [], None
    if agent == "elasticsearch-log-analyzer" and capability == "search-log-events":
        required = {
            "source": first_present(params, "source", "log_source", "elasticsearch_source"),
            "from_time": first_present(params, "from_time", "fromTime", "from"),
            "to_time": first_present(params, "to_time", "toTime", "to"),
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            return [], missing, "Sem contrato executavel seguro para logs Elasticsearch; informe source, from_time e to_time."
        command = [
            "run",
            "elasticsearch-log-analyzer",
            "search-log-events",
            "--source",
            str(required["source"]),
            "--from",
            str(required["from_time"]),
            "--to",
            str(required["to_time"]),
        ]
        append_optional(command, "--query", first_present(params, "log_query", "query"))
        append_optional(command, "--service", first_present(params, "service"))
        append_optional(command, "--environment", first_present(params, "environment", "env"))
        append_optional(command, "--level", first_present(params, "level"))
        return command, [], None
    if agent == "aws-cloudwatch-log-analyzer" and capability == "search-log-events":
        required = {
            "region": first_present(params, "region", "aws_region"),
            "log_group": first_present(params, "log_group", "logGroup"),
            "start_time": first_present(params, "start_time", "from_time", "fromTime"),
            "end_time": first_present(params, "end_time", "to_time", "toTime"),
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            return [], missing, "Sem contrato executavel seguro para CloudWatch; informe region, log_group, start_time e end_time."
        command = [
            "run",
            "aws-cloudwatch-log-analyzer",
            "search-log-events",
            "--region",
            str(required["region"]),
            "--log-group",
            str(required["log_group"]),
            "--start-time",
            str(required["start_time"]),
            "--end-time",
            str(required["end_time"]),
        ]
        append_optional(command, "--filter-pattern", first_present(params, "filter_pattern", "log_query", "query"))
        return command, [], None
    if agent in {"postgres-data-analyzer", "sqlserver-data-analyzer"} and capability == "run-readonly-query":
        query = first_present(params, f"{agent.split('-')[0]}_query", "readonly_query", "sql_query", "database_query")
        if not query:
            return [], ["readonly_query"], f"Sem contrato executavel seguro para {agent}; informe query read-only explicita."
        return ["run", agent, "run-readonly-query", "--query", str(query)], [], None
    if agent == "n1-support-agent" and capability == "execute-n1-card-runbook":
        project = (context.get("card") or {}).get("project") or params.get("project")
        card = (context.get("card") or {}).get("id") or params.get("card")
        if not (project and card):
            return [], ["project", "card"], "Sem contrato executavel seguro para re-rodar N1; informe project e card."
        return ["run", "n1-support-agent", "execute-n1-card-runbook", "--project", str(project), "--card", str(card), "--format", "json"], [], None
    return [], ["agent", "capability"], "Agente ou capability especialista sem contrato de execucao N2."


def specialist_params(context: dict[str, Any]) -> dict[str, Any]:
    support = context.get("fixtureSupportContext") or {}
    params: dict[str, Any] = {}
    if isinstance(support, dict):
        nested = support.get("specialistInputs")
        if isinstance(nested, dict):
            params.update(nested)
        params.update({key: value for key, value in support.items() if key != "specialistInputs"})
    entities = context.get("entities") or {}
    params.setdefault("request_id", entities.get("requestId"))
    params.setdefault("correlation_id", entities.get("correlationId"))
    return params


def first_present(values: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = values.get(key)
        if value not in (None, ""):
            return value
    return None


def append_optional(command: list[str], flag: str, value: Any) -> None:
    if value not in (None, ""):
        command.extend([flag, str(value)])


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
