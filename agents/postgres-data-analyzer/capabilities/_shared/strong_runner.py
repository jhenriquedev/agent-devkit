#!/usr/bin/env python3
"""Dispatch runners for stronger Postgres Data Analyzer capabilities."""

from __future__ import annotations

import argparse
from typing import Any

from runner_support import (
    database_line,
    get_repository,
    infer_domain,
    load_fixture,
    print_error,
    render_erd,
    render_generic_table,
    validate_query_offline,
    value_or_dash,
    write_output,
)


def run_capability(capability: str) -> int:
    parser = argparse.ArgumentParser(description=f"Run postgres-data-analyzer/{capability}")
    add_args(parser)
    args = parser.parse_args()
    try:
        payload = load_fixture(args.fixture) if args.fixture else execute(capability, args)
        write_output(render(capability, payload, args), args.output)
    except Exception as exc:
        return print_error(exc)
    return 0


def add_args(parser: argparse.ArgumentParser) -> None:
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
    parser.add_argument("--pattern", default="")
    parser.add_argument("--key-column")
    parser.add_argument("--key-value")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--fixture")
    parser.add_argument("--output")


def execute(capability: str, args: argparse.Namespace) -> dict[str, Any]:
    if capability == "validate-readonly-query":
        require(args.query, "--query")
        return validate_query_offline(args.query, args.limit)
    repo = get_repository(args.database)
    if capability == "list-databases":
        return repo.list_databases(limit=args.limit)
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
    if capability == "analyze-query-result":
        require(args.query, "--query")
        return repo.analyze_query_result(rows=repo.run_readonly_query(query=args.query, limit=args.limit)["rows"])
    if capability == "detect-data-quality-issues":
        require(args.schema, "--schema")
        require(args.table, "--table")
        return repo.detect_data_quality_issues(schema=args.schema, table=args.table)
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
    raise ValueError(f"unsupported capability: {capability}")


def render(capability: str, payload: dict[str, Any], args: argparse.Namespace) -> str:
    title = TITLE_BY_CAPABILITY.get(capability, capability.replace("-", " ").title())
    lines = [f"# Postgres {title}", "", database_line(payload, args.database)]
    if capability == "validate-readonly-query":
        lines.extend(["- Valid: yes", "", "```sql", payload.get("query") or "", "```"])
    elif capability == "generate-erd-report":
        lines.extend(["", *render_erd(payload.get("relationships") or [])])
    elif capability == "explore-database-domain":
        lines.extend(["", "## Domains", "", *render_generic_table(payload.get("domains") or []), "", "## Tables", "", *render_generic_table(payload.get("tables") or [])])
    else:
        rows = first_rows(payload)
        if rows:
            lines.extend(["", *render_generic_table(rows)])
        else:
            lines.extend(render_key_values(payload))
    return "\n".join(lines).rstrip() + "\n"


def first_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("databases", "relationships", "suggestions", "tables", "columns", "issues", "rows", "plan"):
        if isinstance(payload.get(key), list):
            return payload[key]
    if isinstance(payload.get("columns"), list):
        return payload["columns"]
    return []


def render_key_values(payload: dict[str, Any]) -> list[str]:
    return [f"- {key}: {value_or_dash(value)}" for key, value in payload.items() if not isinstance(value, (list, dict))]


def explore_from_repo(repo: Any, args: argparse.Namespace) -> dict[str, Any]:
    tables = repo.list_tables(schema=args.schema, limit=args.limit)["tables"]
    domains: dict[str, int] = {}
    for table in tables:
        domain = infer_domain(str(table.get("table_name") or ""))
        domains[domain] = domains.get(domain, 0) + 1
    return {"database": repo.database, "domains": [{"domain": key, "table_count": value} for key, value in sorted(domains.items())], "tables": tables}


def require(value: Any, name: str) -> None:
    if not value:
        raise ValueError(f"{name} is required")


TITLE_BY_CAPABILITY = {
    "list-databases": "Databases",
    "list-relationships": "Relationships",
    "suggest-joins": "Join Suggestions",
    "search-tables": "Table Search",
    "search-columns": "Column Search",
    "explore-database-domain": "Database Domain Exploration",
    "generate-erd-report": "ERD Report",
    "validate-readonly-query": "Read-Only Query Validation",
    "build-analysis-query": "Analysis Query Builder",
    "explain-query-plan": "Query Plan",
    "sample-table": "Table Sample",
    "analyze-query-result": "Query Result Analysis",
    "detect-data-quality-issues": "Data Quality Issues",
    "estimate-table-size": "Table Size Estimate",
    "compare-tables": "Table Comparison",
    "trace-record": "Record Trace",
}
