#!/usr/bin/env python3
"""Runner for analyze-restrictive-base."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from runner_support import (  # noqa: E402
    ROOT,
    clean_text,
    load_fixture,
    mask_cpf,
    print_error,
    truncate,
    write_output,
)


CLI = ROOT / "ai-devkit"
DEFAULT_LIMIT = 20
DEFAULT_COLUMN_LIMIT = 200
RESTRICTIVE_TERMS = (
    "restrict",
    "restrit",
    "block",
    "bloq",
    "black",
    "imped",
    "deny",
    "neg",
    "fraud",
)
CPF_COLUMN_TERMS = ("cpf", "document", "documento", "tax")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run n1-support-agent/analyze-restrictive-base")
    parser.add_argument("--cpf")
    parser.add_argument("--database")
    parser.add_argument("--schema")
    parser.add_argument("--table")
    parser.add_argument("--cpf-column")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    try:
        payload = analyze(args)
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render(payload)
        write_output(content, args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def analyze(args: argparse.Namespace) -> dict[str, Any]:
    fixture = load_fixture(args.fixture) if args.fixture else None
    cpf = args.cpf or (fixture or {}).get("cpf")
    cpf_digits = normalize_cpf(cpf)
    if not cpf_digits:
        return base_payload(cpf_digits=None, status="skipped", reason="CPF was not provided or is invalid")

    if fixture:
        return payload_from_fixture(fixture, cpf_digits)

    env = sqlserver_env_override()
    candidates = explicit_candidates(args) or discover_candidates(args, env)
    if not candidates:
        return base_payload(
            cpf_digits=cpf_digits,
            status="unavailable",
            reason="No CPF columns were found for restrictive-base analysis",
        )

    findings: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    checked: list[dict[str, str]] = []
    for candidate in candidates[: int(args.limit or DEFAULT_LIMIT)]:
        checked.append(candidate)
        try:
            result = run_candidate_query(candidate, cpf_digits, args, env)
        except Exception as exc:  # keep the N1 runbook resilient to one bad table
            errors.append({**candidate, "error": truncate(str(exc), 240)})
            continue
        if result["rowCount"]:
            findings.append(result)

    if findings:
        status = "hit"
        reason = "CPF found in restrictive base"
    elif checked and len(errors) < len(checked):
        status = "clear"
        reason = "CPF was not found in checked restrictive-base candidates"
    else:
        status = "unavailable"
        reason = "Restrictive-base candidates could not be queried"

    payload = base_payload(cpf_digits=cpf_digits, status=status, reason=reason)
    payload.update(
        {
            "candidatesChecked": checked,
            "findings": findings,
            "errors": errors,
        }
    )
    return payload


def payload_from_fixture(fixture: dict[str, Any], cpf_digits: str) -> dict[str, Any]:
    status = fixture.get("checkStatus") or ("hit" if fixture.get("findings") else "clear")
    payload = base_payload(cpf_digits=cpf_digits, status=status, reason=fixture.get("reason"))
    payload.update(
        {
            "candidatesChecked": fixture.get("candidatesChecked") or [],
            "findings": mask_findings(fixture.get("findings") or []),
            "errors": fixture.get("errors") or [],
        }
    )
    return payload


def base_payload(cpf_digits: str | None, status: str, reason: str | None) -> dict[str, Any]:
    return {
        "capability": "analyze-restrictive-base",
        "status": "completed" if status in {"hit", "clear", "skipped"} else "unavailable",
        "checkStatus": status,
        "cpfMasked": mask_cpf(cpf_digits) if cpf_digits else None,
        "reason": reason or "-",
        "agent": "n1-support-agent",
        "orchestratedAgent": "sqlserver-data-analyzer",
        "orchestratedCapability": "run-readonly-query",
        "candidatesChecked": [],
        "findings": [],
        "errors": [],
    }


def discover_candidates(args: argparse.Namespace, env: dict[str, str]) -> list[dict[str, str]]:
    command = [
        "run",
        "sqlserver-data-analyzer",
        "search-columns",
        "--pattern",
        "cpf",
        "--limit",
        str(DEFAULT_COLUMN_LIMIT),
        "--format",
        "json",
    ]
    if args.database:
        command.extend(["--database", args.database])
    if args.schema:
        command.extend(["--schema", args.schema])
    payload = run_ai_devkit_json(command, env)
    rows = payload.get("columns") or []
    candidates = [
        {
            "sourceTable": f"{row.get('table_schema')}.{row.get('table_name')}",
            "schema": str(row.get("table_schema") or ""),
            "table": str(row.get("table_name") or ""),
            "cpfColumn": str(row.get("column_name") or ""),
        }
        for row in rows
        if is_candidate_column(row)
    ]
    candidates.sort(key=candidate_priority)
    return candidates


def explicit_candidates(args: argparse.Namespace) -> list[dict[str, str]]:
    if not (args.schema and args.table and args.cpf_column):
        return []
    return [
        {
            "sourceTable": f"{args.schema}.{args.table}",
            "schema": args.schema,
            "table": args.table,
            "cpfColumn": args.cpf_column,
        }
    ]


def run_candidate_query(
    candidate: dict[str, str],
    cpf_digits: str,
    args: argparse.Namespace,
    env: dict[str, str],
) -> dict[str, Any]:
    query = build_candidate_query(candidate, cpf_digits, args.limit)
    command = [
        "run",
        "sqlserver-data-analyzer",
        "run-readonly-query",
        "--query",
        query,
        "--limit",
        str(args.limit),
        "--format",
        "json",
    ]
    if args.database:
        command.extend(["--database", args.database])
    payload = run_ai_devkit_json(command, env)
    rows = payload.get("rows") or []
    return {
        "sourceTable": candidate["sourceTable"],
        "cpfColumn": candidate["cpfColumn"],
        "rowCount": int(payload.get("row_count") or len(rows)),
        "rows": mask_rows(rows),
    }


def build_candidate_query(candidate: dict[str, str], cpf_digits: str, limit: int) -> str:
    schema = quote_identifier(candidate["schema"])
    table = quote_identifier(candidate["table"])
    column = quote_identifier(candidate["cpfColumn"])
    literal = sql_literal(cpf_digits)
    return (
        f"select top ({int(limit)}) * from {schema}.{table} "
        f"where replace(replace(replace(cast({column} as varchar(32)), '.', ''), '-', ''), ' ', '') = {literal}"
    )


def run_ai_devkit_json(args: list[str], env_override: dict[str, str]) -> dict[str, Any]:
    process_env = os.environ.copy()
    process_env.update(env_override)
    process = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=process_env,
    )
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or f"ai-devkit failed: {' '.join(args)}")
    return json.loads(process.stdout)


def sqlserver_env_override() -> dict[str, str]:
    load_root_dotenv()
    connection = os.environ.get("DB_RESTRICTIVE_CONN_STRING") or os.environ.get("SQLSERVER_DB_CONN_STRING")
    return {"SQLSERVER_DB_CONN_STRING": connection} if connection else {}


def load_root_dotenv() -> None:
    dotenv = ROOT / ".env"
    if not dotenv.exists():
        return
    for raw_line in dotenv.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def is_candidate_column(row: dict[str, Any]) -> bool:
    column = str(row.get("column_name") or "").lower()
    return any(term in column for term in CPF_COLUMN_TERMS)


def candidate_priority(candidate: dict[str, str]) -> tuple[int, str]:
    name = f"{candidate.get('sourceTable', '')}.{candidate.get('cpfColumn', '')}".lower()
    priority = 0 if any(term in name for term in RESTRICTIVE_TERMS) else 1
    return priority, name


def mask_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **finding,
            "rows": mask_rows(finding.get("rows") or []),
        }
        for finding in findings
    ]


def mask_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: mask_value(key, value) for key, value in row.items()} for row in rows]


def mask_value(key: str, value: Any) -> Any:
    if value is None:
        return None
    text = str(value)
    if "cpf" in key.lower() or re.fullmatch(r"\D*\d{3}\D*\d{3}\D*\d{3}\D*\d{2}\D*", text):
        return mask_cpf(text)
    return clean_text(value)


def normalize_cpf(value: Any) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits if len(digits) == 11 else None


def quote_identifier(value: str) -> str:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_@$#]*$", value or ""):
        raise ValueError(f"invalid SQL identifier: {value}")
    return "[" + value.replace("]", "]]") + "]"


def sql_literal(value: str) -> str:
    return "N'" + value.replace("'", "''") + "'"


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# N1 Restrictive Base Analysis",
        "",
        f"- Status: {payload.get('checkStatus')}",
        f"- CPF: {payload.get('cpfMasked') or '-'}",
        f"- Reason: {payload.get('reason') or '-'}",
        f"- Candidates checked: {len(payload.get('candidatesChecked') or [])}",
        f"- Findings: {len(payload.get('findings') or [])}",
        "",
    ]
    findings = payload.get("findings") or []
    if findings:
        lines.extend(["## Findings", ""])
        for finding in findings:
            lines.append(
                f"- {finding.get('sourceTable')} / {finding.get('cpfColumn')}: "
                f"{finding.get('rowCount')} row(s)"
            )
    errors = payload.get("errors") or []
    if errors:
        lines.extend(["", "## Errors", ""])
        for error in errors:
            lines.append(f"- {error.get('sourceTable')}: {error.get('error')}")
    lines.extend(["", "## Contract", "", "```json", json.dumps(payload, ensure_ascii=False, indent=2), "```"])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
