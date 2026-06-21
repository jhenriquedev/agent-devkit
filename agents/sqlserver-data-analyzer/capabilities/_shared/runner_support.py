#!/usr/bin/env python3
"""Shared helpers for SQL Server Data Analyzer runners."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
SQLSERVER_DIR = AGENT_DIR / "infra" / "integrations" / "sqlserver"

sys.path.insert(0, str(SQLSERVER_DIR))

from sqlserver_repository import (  # pylint: disable=import-error
    SqlServerRepository,
    analyze_rows,
    enforce_top,
    validate_readonly_query,
)


def run_capability(capability: str) -> int:
    parser = argparse.ArgumentParser(description=f"Run sqlserver-data-analyzer/{capability}")
    add_common_args(parser)
    args = parser.parse_args()
    try:
        payload = load_fixture(args.fixture) if args.fixture else execute(capability, args)
        write_output(render(capability, payload), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--database")
    parser.add_argument("--schema")
    parser.add_argument("--table")
    parser.add_argument("--left-schema")
    parser.add_argument("--left-table")
    parser.add_argument("--right-schema")
    parser.add_argument("--right-table")
    parser.add_argument("--column")
    parser.add_argument("--columns")
    parser.add_argument("--query")
    parser.add_argument("--question")
    parser.add_argument("--pattern", default="")
    parser.add_argument("--key-column")
    parser.add_argument("--key-value")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--fixture")
    parser.add_argument("--output")


def execute(capability: str, args: argparse.Namespace) -> dict[str, Any]:
    if capability == "validate-readonly-query":
        require(args.query, "--query")
        safe_query = enforce_top(validate_readonly_query(args.query), args.limit)
        return {"valid": True, "query": safe_query, "limit": args.limit}
    repo = SqlServerRepository(database=args.database)
    if capability == "test-connection":
        return repo.test_connection()
    if capability == "list-databases":
        return repo.list_databases(limit=args.limit)
    if capability == "list-schemas":
        return repo.list_schemas()
    if capability == "list-tables":
        return repo.list_tables(schema=args.schema, limit=args.limit)
    if capability == "describe-table":
        require(args.schema, "--schema")
        require(args.table, "--table")
        return repo.describe_table(schema=args.schema, table=args.table)
    if capability == "list-relationships":
        return repo.list_relationships(schema=args.schema, limit=args.limit)
    if capability == "suggest-joins":
        return repo.suggest_joins(schema=args.schema)
    if capability == "search-tables":
        return repo.search_tables(pattern=args.pattern, limit=args.limit)
    if capability == "search-columns":
        return repo.search_columns(pattern=args.pattern, schema=args.schema, limit=args.limit)
    if capability == "explore-database-domain":
        return explore_from_repo(repo, args)
    if capability == "generate-erd-report":
        return repo.list_relationships(schema=args.schema, limit=args.limit)
    if capability == "run-readonly-query":
        require(args.query, "--query")
        return repo.run_readonly_query(query=args.query, limit=args.limit)
    if capability == "build-analysis-query":
        require(args.schema, "--schema")
        require(args.table, "--table")
        columns = [item.strip() for item in (args.columns or "").split(",") if item.strip()]
        return repo.build_analysis_query(schema=args.schema, table=args.table, columns=columns, limit=args.limit)
    if capability == "explain-query-plan":
        require(args.query, "--query")
        return repo.explain_query_plan(query=args.query)
    if capability == "sample-table":
        require(args.schema, "--schema")
        require(args.table, "--table")
        return repo.sample_table(schema=args.schema, table=args.table, limit=args.limit)
    if capability == "profile-table":
        require(args.schema, "--schema")
        require(args.table, "--table")
        return repo.profile_table(schema=args.schema, table=args.table)
    if capability == "analyze-query-result":
        require(args.query, "--query")
        return repo.analyze_query_result(rows=repo.run_readonly_query(query=args.query, limit=args.limit)["rows"])
    if capability == "detect-sensitive-columns":
        return repo.detect_sensitive_columns(schema=args.schema)
    if capability == "detect-data-quality-issues":
        require(args.schema, "--schema")
        require(args.table, "--table")
        return repo.detect_data_quality_issues(schema=args.schema, table=args.table)
    if capability == "analyze-cpf-column":
        require(args.schema, "--schema")
        require(args.table, "--table")
        require(args.column, "--column")
        return repo.analyze_cpf_column(schema=args.schema, table=args.table, column=args.column)
    if capability == "estimate-table-size":
        return repo.estimate_table_size(schema=args.schema, limit=args.limit)
    if capability == "compare-tables":
        return repo.compare_tables(
            left_schema=args.left_schema or args.schema,
            left_table=args.left_table or args.table,
            right_schema=args.right_schema,
            right_table=args.right_table,
        )
    if capability == "trace-record":
        require(args.schema, "--schema")
        require(args.table, "--table")
        require(args.key_column, "--key-column")
        require(args.key_value, "--key-value")
        return repo.trace_record(schema=args.schema, table=args.table, key_column=args.key_column, key_value=args.key_value)
    if capability == "generate-data-report":
        return generate_report_from_repo(repo, args)
    raise ValueError(f"unsupported capability: {capability}")


def render(capability: str, payload: dict[str, Any]) -> str:
    title = TITLE_BY_CAPABILITY.get(capability, capability.replace("-", " ").title())
    lines = [f"# SQL Server {title}", ""]
    if capability == "run-readonly-query":
        lines.extend([f"- Row count: {value_or_dash(payload.get('row_count'))}", f"- Limit: {value_or_dash(payload.get('limit'))}", ""])
        lines.extend(render_table(payload.get("rows") or []))
    elif capability == "suggest-joins":
        lines.extend(render_table(payload.get("suggestions") or []))
    elif capability == "validate-readonly-query":
        lines.extend(["- Valid: True", "", "```sql", payload.get("query") or "", "```"])
    elif capability == "generate-erd-report":
        lines.extend(render_erd(payload.get("relationships") or []))
    elif capability == "analyze-query-result":
        lines.extend(render_table(payload.get("columns") or []))
    elif capability == "generate-data-report":
        lines.extend(render_report(payload))
    else:
        rows = first_rows(payload)
        if rows:
            lines.extend(render_table(rows))
        else:
            lines.extend(render_key_values(payload))
    return "\n".join(lines).rstrip() + "\n"


def first_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in (
        "databases",
        "schemas",
        "tables",
        "columns",
        "indexes",
        "constraints",
        "relationships",
        "issues",
        "rows",
    ):
        if isinstance(payload.get(key), list):
            return payload[key]
    return []


def render_key_values(payload: dict[str, Any]) -> list[str]:
    return [f"- {key}: {value_or_dash(value)}" for key, value in payload.items() if not isinstance(value, list | dict)]


def render_table(rows: list[dict[str, Any]], limit: int = 30) -> list[str]:
    if not rows:
        return ["| - |", "|---|", "| No rows. |"]
    columns = list(rows[0].keys())
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    for row in rows[:limit]:
        lines.append("| " + " | ".join(mask_if_sensitive(column, row.get(column)) for column in columns) + " |")
    return lines


def render_erd(relationships: list[dict[str, Any]]) -> list[str]:
    lines = ["```mermaid", "erDiagram"]
    if not relationships:
        lines.append('  EMPTY["No relationships detected"]')
    for row in relationships:
        parent = sanitize_mermaid(row.get("parent_table"))
        referenced = sanitize_mermaid(row.get("referenced_table"))
        lines.append(f"  {parent} }}o--|| {referenced} : {row.get('relationship_name') or 'fk'}")
    lines.append("```")
    return lines


def render_report(payload: dict[str, Any]) -> list[str]:
    lines = ["## Summary", ""]
    for key, value in payload.items():
        if isinstance(value, list):
            lines.extend(["", f"## {key.replace('_', ' ').title()}", "", *render_table(value)])
        elif isinstance(value, dict):
            lines.extend(["", f"## {key.replace('_', ' ').title()}", "", *render_key_values(value)])
        else:
            lines.append(f"- {key}: {value_or_dash(value)}")
    return lines


def explore_from_repo(repo: Any, args: argparse.Namespace) -> dict[str, Any]:
    tables = repo.list_tables(schema=args.schema, limit=args.limit)["tables"]
    domains: dict[str, int] = {}
    for table in tables:
        name = str(table.get("table_name", "")).lower()
        domain = infer_domain(name)
        domains[domain] = domains.get(domain, 0) + 1
    return {"domains": [{"domain": key, "table_count": value} for key, value in sorted(domains.items())], "tables": tables}


def generate_report_from_repo(repo: Any, args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if args.schema and args.table:
        payload["profile"] = repo.profile_table(schema=args.schema, table=args.table)
        payload["quality_issues"] = repo.detect_data_quality_issues(schema=args.schema, table=args.table)["issues"]
    payload["sensitive_columns"] = repo.detect_sensitive_columns(schema=args.schema)["columns"]
    payload["relationships"] = repo.list_relationships(schema=args.schema)["relationships"]
    return payload


def infer_domain(table_name: str) -> str:
    groups = {
        "customer": ["customer", "client", "cliente", "person", "pessoa"],
        "sales": ["order", "pedido", "sale", "invoice", "fatura"],
        "finance": ["payment", "pagamento", "ledger", "account"],
        "audit": ["log", "audit", "history", "evento"],
        "security": ["user", "role", "permission", "auth"],
    }
    for domain, terms in groups.items():
        if any(term in table_name for term in terms):
            return domain
    return "other"


def mask_if_sensitive(column: str, value: Any) -> str:
    text = value_or_dash(value)
    lowered = column.lower()
    if "cpf" in lowered or "document" in lowered:
        return mask_cpf(text)
    if "email" in lowered or "mail" in lowered:
        return mask_email(text)
    if any(term in lowered for term in ("token", "secret", "password", "senha")):
        return "***"
    return text


def mask_cpf(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 11:
        return value
    return f"{digits[:3]}.***.***-{digits[-2:]}"


def mask_email(value: str) -> str:
    if "@" not in value:
        return value
    left, right = value.split("@", 1)
    return f"{left[:2]}***@{right}"


def sanitize_mermaid(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", str(value or "unknown"))


def value_or_dash(value: Any) -> str:
    if value is None:
        return "-"
    text = " ".join(str(value).replace("\r", " ").replace("\n", " ").split())
    return text if text else "-"


def load_fixture(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_output(markdown: str, output: str | None) -> None:
    if output:
        Path(output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)


def print_error(exc: Exception) -> int:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1


def require(value: Any, name: str) -> None:
    if not value:
        raise ValueError(f"{name} is required")


TITLE_BY_CAPABILITY = {
    "test-connection": "Connection",
    "list-databases": "Databases",
    "list-schemas": "Schemas",
    "list-tables": "Tables",
    "describe-table": "Table Description",
    "list-relationships": "Relationships",
    "suggest-joins": "Join Suggestions",
    "search-tables": "Table Search",
    "search-columns": "Column Search",
    "explore-database-domain": "Database Domain Exploration",
    "generate-erd-report": "ERD Report",
    "run-readonly-query": "Read-Only Query",
    "validate-readonly-query": "Read-Only Query Validation",
    "build-analysis-query": "Analysis Query Builder",
    "explain-query-plan": "Query Plan",
    "sample-table": "Table Sample",
    "profile-table": "Table Profile",
    "analyze-query-result": "Query Result Analysis",
    "detect-sensitive-columns": "Sensitive Columns",
    "detect-data-quality-issues": "Data Quality Issues",
    "analyze-cpf-column": "CPF Analysis",
    "estimate-table-size": "Table Size Estimate",
    "compare-tables": "Table Comparison",
    "trace-record": "Record Trace",
    "generate-data-report": "Data Report",
}
