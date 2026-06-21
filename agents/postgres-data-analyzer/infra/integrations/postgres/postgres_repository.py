#!/usr/bin/env python3
"""Read-only Postgres repository backed by psql."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class PostgresRepositoryError(RuntimeError):
    """Raised when psql calls fail or a query is unsafe."""


@dataclass(frozen=True)
class PostgresConfig:
    connection_string: str
    statement_timeout_ms: int = 15000

    @classmethod
    def from_env(cls, database: str | None = None) -> "PostgresConfig":
        load_dotenv()
        connection = os.environ.get("POSTGRES_DB_CONN_STRING") or os.environ.get("DATABASE_URL")
        if not connection:
            raise PostgresRepositoryError("POSTGRES_DB_CONN_STRING is required")
        return cls(
            connection_string=with_database_override(connection, database),
            statement_timeout_ms=int(os.environ.get("POSTGRES_STATEMENT_TIMEOUT", "15000")),
        )


class PostgresRepository:
    """Small read-only repository for Postgres data analysis."""

    def __init__(self, config: PostgresConfig | None = None, database: str | None = None) -> None:
        self.config = config or PostgresConfig.from_env(database=database)

    @property
    def database(self) -> str | None:
        return connection_database(self.config.connection_string)

    def test_connection(self) -> dict[str, Any]:
        rows = self._query_json(
            """
            select
              version() as version,
              current_database() as database,
              current_user as user_name,
              current_schema() as current_schema
            """
        )
        return rows[0] if rows else {}

    def list_schemas(self) -> dict[str, Any]:
        rows = self._query_json(
            """
            select schema_name
            from information_schema.schemata
            where schema_name not like 'pg_%'
              and schema_name <> 'information_schema'
            order by schema_name
            """
        )
        return {"database": self.database, "count": len(rows), "schemas": rows}

    def list_tables(self, *, schema: str | None = None, limit: int = 200) -> dict[str, Any]:
        where = "and table_schema = " + sql_literal(schema) if schema else ""
        rows = self._query_json(
            f"""
            select table_schema, table_name, table_type
            from information_schema.tables
            where table_schema not like 'pg_%'
              and table_schema <> 'information_schema'
              {where}
            order by table_schema, table_name
            limit {int(limit)}
            """
        )
        return {"database": self.database, "schema": schema, "count": len(rows), "tables": rows}

    def describe_table(self, *, schema: str, table: str) -> dict[str, Any]:
        validate_identifier(schema, "schema")
        validate_identifier(table, "table")
        columns = self._query_json(
            f"""
            select column_name, data_type, udt_name, is_nullable, column_default
            from information_schema.columns
            where table_schema = {sql_literal(schema)}
              and table_name = {sql_literal(table)}
            order by ordinal_position
            """
        )
        indexes = self._query_json(
            f"""
            select indexname, indexdef
            from pg_indexes
            where schemaname = {sql_literal(schema)}
              and tablename = {sql_literal(table)}
            order by indexname
            """
        )
        constraints = self._query_json(
            f"""
            select constraint_name, constraint_type
            from information_schema.table_constraints
            where table_schema = {sql_literal(schema)}
              and table_name = {sql_literal(table)}
            order by constraint_name
            """
        )
        return {
            "database": self.database,
            "schema": schema,
            "table": table,
            "columns": columns,
            "indexes": indexes,
            "constraints": constraints,
        }

    def run_readonly_query(self, *, query: str, limit: int = 100) -> dict[str, Any]:
        safe_query = enforce_limit(validate_readonly_query(query), limit)
        rows = self._query_json(safe_query)
        return {"database": self.database, "limit": limit, "row_count": len(rows), "rows": rows, "query": safe_query}

    def profile_table(self, *, schema: str, table: str, limit_columns: int = 30) -> dict[str, Any]:
        description = self.describe_table(schema=schema, table=table)
        columns = description["columns"][:limit_columns]
        qualified = qualified_name(schema, table)
        row_count = self._query_json(f"select count(*)::bigint as count from {qualified}")[0]["count"]
        profiles = []
        for column in columns:
            name = column["column_name"]
            ident = quote_ident(name)
            stats = self._query_json(
                f"""
                select
                  {sql_literal(name)} as column_name,
                  count(*)::bigint as total_rows,
                  count(*) filter (where {ident} is null)::bigint as null_count,
                  count(distinct {ident})::bigint as distinct_count
                from {qualified}
                """
            )[0]
            profiles.append({**column, **stats})
        return {"database": self.database, "schema": schema, "table": table, "row_count": row_count, "columns": profiles}

    def detect_sensitive_columns(self, *, schema: str | None = None) -> dict[str, Any]:
        where = "and table_schema = " + sql_literal(schema) if schema else ""
        rows = self._query_json(
            f"""
            select table_schema, table_name, column_name, data_type
            from information_schema.columns
            where table_schema not like 'pg_%'
              and table_schema <> 'information_schema'
              {where}
            order by table_schema, table_name, ordinal_position
            """
        )
        findings = []
        for row in rows:
            kind = sensitive_kind(row["column_name"])
            if kind:
                findings.append({**row, "sensitive_kind": kind})
        return {"database": self.database, "schema": schema, "count": len(findings), "columns": findings}

    def analyze_cpf_column(self, *, schema: str, table: str, column: str) -> dict[str, Any]:
        validate_identifier(schema, "schema")
        validate_identifier(table, "table")
        validate_identifier(column, "column")
        qualified = qualified_name(schema, table)
        col = quote_ident(column)
        rows = self._query_json(
            f"""
            with normalized as (
              select regexp_replace(coalesce({col}::text, ''), '\\D', '', 'g') as cpf
              from {qualified}
            ),
            checked as (
              select
                cpf,
                case
                  when cpf ~ '^\\d{{11}}$'
                   and cpf !~ '^(\\d)\\1{{10}}$'
                   and (((
                     substring(cpf,1,1)::int * 10 +
                     substring(cpf,2,1)::int * 9 +
                     substring(cpf,3,1)::int * 8 +
                     substring(cpf,4,1)::int * 7 +
                     substring(cpf,5,1)::int * 6 +
                     substring(cpf,6,1)::int * 5 +
                     substring(cpf,7,1)::int * 4 +
                     substring(cpf,8,1)::int * 3 +
                     substring(cpf,9,1)::int * 2
                   ) * 10) % 11) % 10 = substring(cpf,10,1)::int
                   and (((
                     substring(cpf,1,1)::int * 11 +
                     substring(cpf,2,1)::int * 10 +
                     substring(cpf,3,1)::int * 9 +
                     substring(cpf,4,1)::int * 8 +
                     substring(cpf,5,1)::int * 7 +
                     substring(cpf,6,1)::int * 6 +
                     substring(cpf,7,1)::int * 5 +
                     substring(cpf,8,1)::int * 4 +
                     substring(cpf,9,1)::int * 3 +
                     substring(cpf,10,1)::int * 2
                   ) * 10) % 11) % 10 = substring(cpf,11,1)::int
                  then true else false
                end as is_valid
              from normalized
            ),
            duplicate_cpfs as (
              select cpf, count(*) as occurrences
              from checked
              where cpf ~ '^\\d{{11}}$'
              group by cpf
              having count(*) > 1
            )
            select
              (select count(*)::bigint from checked) as total_rows,
              (select count(*)::bigint from checked where cpf = '') as blank_count,
              (select count(*)::bigint from checked where cpf !~ '^\\d{{11}}$' and cpf <> '') as invalid_format_count,
              (select count(*)::bigint from checked where cpf ~ '^(\\d)\\1{{10}}$') as repeated_digits_count,
              (select count(*)::bigint from checked where is_valid) as valid_count,
              (select count(*)::bigint from checked where not is_valid and cpf ~ '^\\d{{11}}$') as invalid_check_digit_count,
              (select count(*)::bigint from duplicate_cpfs) as duplicated_document_count,
              (select coalesce(sum(occurrences), 0)::bigint from duplicate_cpfs) as duplicated_row_count
            """
        )[0]
        return {"database": self.database, "schema": schema, "table": table, "column": column, **rows}

    def _query_json(self, query: str) -> list[dict[str, Any]]:
        sql = f"""
        set statement_timeout = {int(self.config.statement_timeout_ms)};
        copy (
          select coalesce(json_agg(row_to_json(q)), '[]'::json)
          from (
            {query.strip().rstrip(';')}
          ) q
        ) to stdout;
        """
        output = self._psql(sql)
        text = output.strip() or "[]"
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise PostgresRepositoryError(f"invalid psql json output: {exc}") from exc

    def _psql(self, sql: str) -> str:
        env = os.environ.copy()
        command = ["psql", "-X", "-q", "-t", "-A", "-v", "ON_ERROR_STOP=1", "-f", "-"]
        extra_env = connection_env(self.config.connection_string)
        if extra_env:
            env.update(extra_env)
        else:
            command.insert(1, self.config.connection_string)
        result = subprocess.run(
            command,
            input=sql,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        if result.returncode != 0:
            raise PostgresRepositoryError(result.stderr.strip() or "psql failed")
        return result.stdout


BLOCKED_SQL = re.compile(r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|vacuum|call|do|copy)\b", re.I)


def validate_readonly_query(query: str) -> str:
    text = query.strip().rstrip(";")
    lowered = text.lower()
    if not (lowered.startswith("select") or lowered.startswith("with") or lowered.startswith("explain")):
        raise PostgresRepositoryError("only SELECT, WITH, or EXPLAIN queries are allowed")
    if BLOCKED_SQL.search(text):
        raise PostgresRepositoryError("query contains blocked SQL keyword")
    return text


def enforce_limit(query: str, limit: int) -> str:
    if re.search(r"\blimit\s+\d+\b", query, re.I):
        return query
    return f"select * from ({query}) readonly_query limit {int(limit)}"


def connection_env(connection: str) -> dict[str, str]:
    parsed = urllib.parse.urlparse(connection)
    if parsed.scheme not in {"postgres", "postgresql"}:
        return {}
    env: dict[str, str] = {}
    if parsed.hostname:
        env["PGHOST"] = parsed.hostname
    if parsed.port:
        env["PGPORT"] = str(parsed.port)
    if parsed.username:
        env["PGUSER"] = urllib.parse.unquote(parsed.username)
    if parsed.password:
        env["PGPASSWORD"] = urllib.parse.unquote(parsed.password)
    if parsed.path and parsed.path != "/":
        env["PGDATABASE"] = urllib.parse.unquote(parsed.path.lstrip("/"))
    query = urllib.parse.parse_qs(parsed.query)
    if "sslmode" in query:
        env["PGSSLMODE"] = query["sslmode"][0]
    return env


def connection_database(connection: str) -> str | None:
    parsed = urllib.parse.urlparse(connection)
    if parsed.path and parsed.path != "/":
        return urllib.parse.unquote(parsed.path.lstrip("/"))
    return None


def with_database_override(connection: str, database: str | None) -> str:
    if not database:
        return connection
    validate_database_name(database)
    parsed = urllib.parse.urlparse(connection)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise PostgresRepositoryError("database override requires a postgres connection URL")
    return urllib.parse.urlunparse(parsed._replace(path="/" + urllib.parse.quote(database, safe="")))


def validate_database_name(value: str) -> None:
    if not re.match(r"^[A-Za-z0-9_-]+$", value or ""):
        raise PostgresRepositoryError("invalid database name")


def validate_identifier(value: str, label: str) -> None:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", value or ""):
        raise PostgresRepositoryError(f"invalid {label} identifier")


def quote_ident(value: str) -> str:
    validate_identifier(value, "identifier")
    return f'"{value}"'


def qualified_name(schema: str, table: str) -> str:
    return f"{quote_ident(schema)}.{quote_ident(table)}"


def sql_literal(value: str | None) -> str:
    if value is None:
        return "null"
    return "'" + value.replace("'", "''") + "'"


def sensitive_kind(column_name: str) -> str | None:
    lowered = column_name.lower()
    patterns = {
        "cpf": ["cpf", "documento", "tax_id"],
        "cnpj": ["cnpj"],
        "email": ["email", "e_mail"],
        "phone": ["telefone", "phone", "celular", "mobile"],
        "name": ["nome", "name", "full_name"],
        "address": ["endereco", "address", "cep", "zipcode"],
    }
    for kind, terms in patterns.items():
        if any(term in lowered for term in terms):
            return kind
    return None


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
