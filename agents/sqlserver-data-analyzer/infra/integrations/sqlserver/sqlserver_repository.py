#!/usr/bin/env python3
"""Read-only SQL Server repository backed by pyodbc."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class SqlServerRepositoryError(RuntimeError):
    """Raised when SQL Server calls fail or a query is unsafe."""


BLOCKED_SQL = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|merge|create|grant|revoke|backup|restore|dbcc|exec|execute)\b",
    re.I,
)


@dataclass(frozen=True)
class SqlServerConfig:
    connection_string: str
    statement_timeout_ms: int = 15000
    lock_timeout_ms: int = 5000
    query_limit: int = 100

    @classmethod
    def from_env(cls, database: str | None = None) -> "SqlServerConfig":
        load_dotenv()
        connection = os.environ.get("SQLSERVER_DB_CONN_STRING") or os.environ.get("MSSQL_DB_CONN_STRING")
        if not connection:
            raise SqlServerRepositoryError("SQLSERVER_DB_CONN_STRING is required")
        return cls(
            connection_string=with_database_override(connection, database),
            statement_timeout_ms=int(os.environ.get("SQLSERVER_STATEMENT_TIMEOUT", "15000")),
            lock_timeout_ms=int(os.environ.get("SQLSERVER_LOCK_TIMEOUT", "5000")),
            query_limit=int(os.environ.get("SQLSERVER_QUERY_LIMIT", "100")),
        )


class SqlServerRepository:
    """Small read-only repository for SQL Server data analysis."""

    def __init__(self, config: SqlServerConfig | None = None, database: str | None = None) -> None:
        self.config = config or SqlServerConfig.from_env(database=database)

    def test_connection(self) -> dict[str, Any]:
        rows = self._query_rows(
            """
            select
              @@version as version,
              db_name() as database_name,
              suser_sname() as user_name,
              schema_name() as current_schema
            """
        )
        return rows[0] if rows else {}

    def list_databases(self, *, limit: int = 200) -> dict[str, Any]:
        rows = self._query_rows(
            f"""
            select top ({int(limit)})
              name as database_name,
              state_desc,
              compatibility_level
            from sys.databases
            where state_desc = 'ONLINE'
            order by name
            """
        )
        return {"count": len(rows), "databases": rows}

    def list_schemas(self) -> dict[str, Any]:
        rows = self._query_rows(
            """
            select name as schema_name
            from sys.schemas
            where name not in ('sys', 'INFORMATION_SCHEMA')
            order by name
            """
        )
        return {"count": len(rows), "schemas": rows}

    def list_tables(self, *, schema: str | None = None, limit: int = 200) -> dict[str, Any]:
        where = f"and s.name = {sql_literal(schema)}" if schema else ""
        rows = self._query_rows(
            f"""
            select top ({int(limit)})
              s.name as table_schema,
              o.name as table_name,
              o.type_desc as table_type,
              o.create_date,
              o.modify_date
            from sys.objects o
            join sys.schemas s on s.schema_id = o.schema_id
            where o.type in ('U', 'V')
              {where}
            order by s.name, o.name
            """
        )
        return {"schema": schema, "count": len(rows), "tables": rows}

    def describe_table(self, *, schema: str, table: str) -> dict[str, Any]:
        validate_identifier(schema, "schema")
        validate_identifier(table, "table")
        columns = self._query_rows(
            f"""
            select
              c.name as column_name,
              t.name as data_type,
              c.max_length,
              c.precision,
              c.scale,
              c.is_nullable,
              c.is_identity,
              dc.definition as column_default
            from sys.columns c
            join sys.types t on t.user_type_id = c.user_type_id
            join sys.objects o on o.object_id = c.object_id
            join sys.schemas s on s.schema_id = o.schema_id
            left join sys.default_constraints dc on dc.object_id = c.default_object_id
            where s.name = {sql_literal(schema)}
              and o.name = {sql_literal(table)}
            order by c.column_id
            """
        )
        indexes = self._query_rows(
            f"""
            select i.name as index_name, i.type_desc, i.is_unique, i.is_primary_key
            from sys.indexes i
            join sys.objects o on o.object_id = i.object_id
            join sys.schemas s on s.schema_id = o.schema_id
            where s.name = {sql_literal(schema)}
              and o.name = {sql_literal(table)}
              and i.name is not null
            order by i.name
            """
        )
        constraints = self._query_rows(
            f"""
            select kc.name as constraint_name, kc.type_desc
            from sys.key_constraints kc
            join sys.objects o on o.object_id = kc.parent_object_id
            join sys.schemas s on s.schema_id = o.schema_id
            where s.name = {sql_literal(schema)}
              and o.name = {sql_literal(table)}
            order by kc.name
            """
        )
        return {"schema": schema, "table": table, "columns": columns, "indexes": indexes, "constraints": constraints}

    def list_relationships(self, *, schema: str | None = None, limit: int = 500) -> dict[str, Any]:
        where = f"and ps.name = {sql_literal(schema)}" if schema else ""
        rows = self._query_rows(
            f"""
            select top ({int(limit)})
              fk.name as relationship_name,
              ps.name + '.' + pt.name as parent_table,
              pc.name as parent_column,
              rs.name + '.' + rt.name as referenced_table,
              rc.name as referenced_column
            from sys.foreign_key_columns fkc
            join sys.foreign_keys fk on fk.object_id = fkc.constraint_object_id
            join sys.tables pt on pt.object_id = fkc.parent_object_id
            join sys.schemas ps on ps.schema_id = pt.schema_id
            join sys.columns pc on pc.object_id = pt.object_id and pc.column_id = fkc.parent_column_id
            join sys.tables rt on rt.object_id = fkc.referenced_object_id
            join sys.schemas rs on rs.schema_id = rt.schema_id
            join sys.columns rc on rc.object_id = rt.object_id and rc.column_id = fkc.referenced_column_id
            where 1 = 1 {where}
            order by parent_table, referenced_table
            """
        )
        return {"schema": schema, "count": len(rows), "relationships": rows}

    def suggest_joins(self, *, schema: str | None = None) -> dict[str, Any]:
        relationships = self.list_relationships(schema=schema)["relationships"]
        suggestions = [
            {
                "left_table": row["parent_table"],
                "left_column": row["parent_column"],
                "right_table": row["referenced_table"],
                "right_column": row["referenced_column"],
                "confidence": "high",
            }
            for row in relationships
        ]
        if not suggestions:
            columns = self.search_columns(pattern="id", schema=schema, limit=500)["columns"]
            suggestions = heuristic_join_suggestions(columns)
        return {"schema": schema, "count": len(suggestions), "suggestions": suggestions}

    def search_tables(self, *, pattern: str, limit: int = 100) -> dict[str, Any]:
        rows = self._query_rows(
            f"""
            select top ({int(limit)})
              s.name as table_schema,
              o.name as table_name,
              o.type_desc as table_type
            from sys.objects o
            join sys.schemas s on s.schema_id = o.schema_id
            where o.type in ('U', 'V')
              and (o.name like {sql_like(pattern)} or s.name like {sql_like(pattern)})
            order by s.name, o.name
            """
        )
        return {"pattern": pattern, "count": len(rows), "tables": rows}

    def search_columns(self, *, pattern: str, schema: str | None = None, limit: int = 200) -> dict[str, Any]:
        where = f"and s.name = {sql_literal(schema)}" if schema else ""
        rows = self._query_rows(
            f"""
            select top ({int(limit)})
              s.name as table_schema,
              o.name as table_name,
              c.name as column_name,
              t.name as data_type
            from sys.columns c
            join sys.types t on t.user_type_id = c.user_type_id
            join sys.objects o on o.object_id = c.object_id
            join sys.schemas s on s.schema_id = o.schema_id
            where o.type in ('U', 'V')
              and (c.name like {sql_like(pattern)} or t.name like {sql_like(pattern)})
              {where}
            order by s.name, o.name, c.column_id
            """
        )
        return {"pattern": pattern, "schema": schema, "count": len(rows), "columns": rows}

    def run_readonly_query(self, *, query: str, limit: int = 100) -> dict[str, Any]:
        safe_query = enforce_top(validate_readonly_query(query), limit)
        rows = self._query_rows(safe_query)
        return {"limit": limit, "row_count": len(rows), "rows": rows, "query": safe_query}

    def validate_readonly_query(self, *, query: str, limit: int = 100) -> dict[str, Any]:
        safe_query = enforce_top(validate_readonly_query(query), limit)
        return {"valid": True, "query": safe_query, "limit": limit}

    def build_analysis_query(self, *, schema: str, table: str, columns: list[str] | None = None, limit: int = 100) -> dict[str, Any]:
        validate_identifier(schema, "schema")
        validate_identifier(table, "table")
        selected = ", ".join(quote_ident(column) for column in columns) if columns else "*"
        query = f"select top ({int(limit)}) {selected} from {qualified_name(schema, table)}"
        return {"query": query, "notes": ["Review filters before execution."]}

    def explain_query_plan(self, *, query: str) -> dict[str, Any]:
        safe_query = validate_readonly_query(query)
        rows = self._query_rows(f"set showplan_text on; {safe_query}; set showplan_text off;")
        return {"query": safe_query, "plan": rows}

    def sample_table(self, *, schema: str, table: str, limit: int = 20) -> dict[str, Any]:
        query = f"select top ({int(limit)}) * from {qualified_name(schema, table)}"
        rows = self._query_rows(query)
        return {"schema": schema, "table": table, "row_count": len(rows), "rows": rows}

    def profile_table(self, *, schema: str, table: str, limit_columns: int = 30) -> dict[str, Any]:
        description = self.describe_table(schema=schema, table=table)
        columns = description["columns"][:limit_columns]
        row_count = self._query_rows(f"select count_big(*) as count from {qualified_name(schema, table)}")[0]["count"]
        profiles = []
        for column in columns:
            name = column["column_name"]
            ident = quote_ident(name)
            stats = self._query_rows(
                f"""
                select
                  {sql_literal(name)} as column_name,
                  count_big(*) as total_rows,
                  sum(case when {ident} is null then 1 else 0 end) as null_count,
                  count_big(distinct {ident}) as distinct_count
                from {qualified_name(schema, table)}
                """
            )[0]
            profiles.append({**column, **stats})
        return {"schema": schema, "table": table, "row_count": row_count, "columns": profiles}

    def analyze_query_result(self, *, rows: list[dict[str, Any]]) -> dict[str, Any]:
        return analyze_rows(rows)

    def detect_sensitive_columns(self, *, schema: str | None = None) -> dict[str, Any]:
        columns = self.search_columns(pattern="", schema=schema, limit=5000)["columns"]
        findings = []
        for row in columns:
            kind = sensitive_kind(row["column_name"])
            if kind:
                findings.append({**row, "sensitive_kind": kind})
        return {"schema": schema, "count": len(findings), "columns": findings}

    def detect_data_quality_issues(self, *, schema: str, table: str) -> dict[str, Any]:
        profile = self.profile_table(schema=schema, table=table)
        issues = []
        for column in profile["columns"]:
            total = int(column.get("total_rows") or 0)
            nulls = int(column.get("null_count") or 0)
            distinct = int(column.get("distinct_count") or 0)
            if total and nulls == total:
                issues.append({"column_name": column["column_name"], "issue": "all_null"})
            if total > 1 and distinct == 1:
                issues.append({"column_name": column["column_name"], "issue": "constant_value"})
        return {"schema": schema, "table": table, "issues": issues}

    def analyze_cpf_column(self, *, schema: str, table: str, column: str) -> dict[str, Any]:
        validate_identifier(column, "column")
        rows = self._query_rows(f"select {quote_ident(column)} as cpf from {qualified_name(schema, table)}")
        return analyze_cpf_values([row.get("cpf") for row in rows], schema=schema, table=table, column=column)

    def estimate_table_size(self, *, schema: str | None = None, limit: int = 200) -> dict[str, Any]:
        where = f"and s.name = {sql_literal(schema)}" if schema else ""
        rows = self._query_rows(
            f"""
            select top ({int(limit)})
              s.name as table_schema,
              t.name as table_name,
              sum(p.rows) as row_count,
              sum(a.total_pages) * 8 as total_kb,
              sum(a.used_pages) * 8 as used_kb
            from sys.tables t
            join sys.schemas s on s.schema_id = t.schema_id
            join sys.indexes i on i.object_id = t.object_id
            join sys.partitions p on p.object_id = i.object_id and p.index_id = i.index_id
            join sys.allocation_units a on a.container_id = p.partition_id
            where 1 = 1 {where}
            group by s.name, t.name
            order by total_kb desc
            """
        )
        return {"schema": schema, "count": len(rows), "tables": rows}

    def compare_tables(self, *, left_schema: str, left_table: str, right_schema: str, right_table: str) -> dict[str, Any]:
        left = self.describe_table(schema=left_schema, table=left_table)
        right = self.describe_table(schema=right_schema, table=right_table)
        left_cols = {column["column_name"]: column["data_type"] for column in left["columns"]}
        right_cols = {column["column_name"]: column["data_type"] for column in right["columns"]}
        return {
            "left": f"{left_schema}.{left_table}",
            "right": f"{right_schema}.{right_table}",
            "common_columns": sorted(set(left_cols) & set(right_cols)),
            "left_only": sorted(set(left_cols) - set(right_cols)),
            "right_only": sorted(set(right_cols) - set(left_cols)),
        }

    def trace_record(self, *, schema: str, table: str, key_column: str, key_value: str) -> dict[str, Any]:
        validate_identifier(key_column, "key_column")
        base = self.run_readonly_query(
            query=f"select * from {qualified_name(schema, table)} where {quote_ident(key_column)} = {sql_literal(key_value)}",
            limit=20,
        )
        relationships = self.list_relationships(schema=schema)["relationships"]
        return {"schema": schema, "table": table, "key_column": key_column, "base_rows": base["rows"], "relationships": relationships}

    def _query_rows(self, query: str) -> list[dict[str, Any]]:
        try:
            import pyodbc  # type: ignore
        except ImportError as exc:
            raise SqlServerRepositoryError("pyodbc is required for real SQL Server calls") from exc
        try:
            with pyodbc.connect(self.config.connection_string, timeout=max(1, self.config.statement_timeout_ms // 1000)) as conn:
                cursor = conn.cursor()
                cursor.execute(f"set lock_timeout {int(self.config.lock_timeout_ms)}")
                cursor.execute(query)
                columns = [column[0] for column in cursor.description or []]
                return [dict(zip(columns, row)) for row in cursor.fetchall()] if columns else []
        except Exception as exc:
            raise SqlServerRepositoryError(str(exc)) from exc


def validate_readonly_query(query: str) -> str:
    text = query.strip().rstrip(";")
    lowered = text.lower()
    if BLOCKED_SQL.search(text):
        raise SqlServerRepositoryError("query contains blocked SQL keyword")
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise SqlServerRepositoryError("only SELECT or WITH queries are allowed")
    return text


def enforce_top(query: str, limit: int) -> str:
    if re.search(r"\btop\s*\(", query, re.I) or re.search(r"\boffset\s+\d+\s+rows\b", query, re.I):
        return query
    match = re.match(r"(?is)^\s*select\s+", query)
    if match:
        return re.sub(r"(?is)^\s*select\s+", f"select top ({int(limit)}) ", query, count=1)
    return f"select top ({int(limit)}) * from ({query}) readonly_query"


def validate_database_name(value: str) -> None:
    if not re.match(r"^[A-Za-z0-9_.-]+$", value or ""):
        raise SqlServerRepositoryError("invalid database name")


def validate_identifier(value: str, label: str) -> None:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_@$#]*$", value or ""):
        raise SqlServerRepositoryError(f"invalid {label} identifier")


def quote_ident(value: str) -> str:
    validate_identifier(value, "identifier")
    return "[" + value.replace("]", "]]") + "]"


def qualified_name(schema: str, table: str) -> str:
    validate_identifier(schema, "schema")
    validate_identifier(table, "table")
    return f"{quote_ident(schema)}.{quote_ident(table)}"


def sql_literal(value: str | None) -> str:
    if value is None:
        return "null"
    return "N'" + value.replace("'", "''") + "'"


def sql_like(value: str) -> str:
    return sql_literal(f"%{value}%")


def with_database_override(connection: str, database: str | None) -> str:
    if not database:
        return connection
    validate_database_name(database)
    parts = [part for part in connection.split(";") if part]
    replaced = False
    output = []
    for part in parts:
        key = part.split("=", 1)[0].strip().lower() if "=" in part else ""
        if key in {"database", "initial catalog"}:
            output.append(f"Database={database}")
            replaced = True
        else:
            output.append(part)
    if not replaced:
        output.append(f"Database={database}")
    return ";".join(output) + ";"


def sensitive_kind(column_name: str) -> str | None:
    lowered = column_name.lower()
    patterns = {
        "cpf": ["cpf", "documento", "tax_id"],
        "cnpj": ["cnpj"],
        "email": ["email", "e_mail", "mail"],
        "phone": ["telefone", "phone", "celular", "mobile"],
        "name": ["nome", "name", "full_name"],
        "address": ["endereco", "address", "cep", "zipcode"],
        "password": ["password", "senha", "passwd"],
        "token": ["token", "secret", "api_key", "apikey"],
    }
    for kind, terms in patterns.items():
        if any(term in lowered for term in terms):
            return kind
    return None


def heuristic_join_suggestions(columns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for column in columns:
        normalized = re.sub(r"(^id$|_?id$)", "", column.get("column_name", "").lower())
        if normalized:
            by_name.setdefault(normalized, []).append(column)
    suggestions = []
    for items in by_name.values():
        if len(items) < 2:
            continue
        left, right = items[0], items[1]
        suggestions.append(
            {
                "left_table": f"{left['table_schema']}.{left['table_name']}",
                "left_column": left["column_name"],
                "right_table": f"{right['table_schema']}.{right['table_name']}",
                "right_column": right["column_name"],
                "confidence": "medium",
            }
        )
    return suggestions


def analyze_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"row_count": 0, "columns": []}
    columns = []
    for key in rows[0].keys():
        values = [row.get(key) for row in rows]
        columns.append(
            {
                "column_name": key,
                "null_count": sum(value is None for value in values),
                "distinct_count": len({str(value) for value in values if value is not None}),
                "sensitive_kind": sensitive_kind(key),
            }
        )
    return {"row_count": len(rows), "columns": columns}


def analyze_cpf_values(values: list[Any], *, schema: str, table: str, column: str) -> dict[str, Any]:
    normalized = [re.sub(r"\D", "", str(value or "")) for value in values]
    valid = [value for value in normalized if is_valid_cpf(value)]
    duplicates = {value for value in normalized if value and normalized.count(value) > 1}
    return {
        "schema": schema,
        "table": table,
        "column": column,
        "total_rows": len(values),
        "blank_count": sum(value == "" for value in normalized),
        "invalid_format_count": sum(value != "" and not re.match(r"^\d{11}$", value) for value in normalized),
        "repeated_digits_count": sum(bool(re.match(r"^(\d)\1{10}$", value)) for value in normalized),
        "valid_count": len(valid),
        "invalid_check_digit_count": sum(bool(re.match(r"^\d{11}$", value)) and not is_valid_cpf(value) for value in normalized),
        "duplicated_document_count": len(duplicates),
        "duplicated_row_count": sum(value in duplicates for value in normalized),
    }


def is_valid_cpf(value: str) -> bool:
    if not re.match(r"^\d{11}$", value) or re.match(r"^(\d)\1{10}$", value):
        return False
    digits = [int(char) for char in value]
    first = (sum(digits[i] * (10 - i) for i in range(9)) * 10 % 11) % 10
    second = (sum(digits[i] * (11 - i) for i in range(10)) * 10 % 11) % 10
    return first == digits[9] and second == digits[10]


def load_dotenv() -> None:
    for candidate in _dotenv_candidates():
        if not candidate.exists():
            continue
        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        return


def _dotenv_candidates() -> list[Path]:
    paths = []
    for start in (Path.cwd(), Path(__file__).resolve()):
        current = start if start.is_dir() else start.parent
        paths.extend(parent / ".env" for parent in [current, *current.parents])
    seen = set()
    unique = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique
