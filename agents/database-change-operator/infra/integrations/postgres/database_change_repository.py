#!/usr/bin/env python3
"""Controlled Postgres change repository backed by psql."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class DatabaseChangeRepositoryError(RuntimeError):
    """Raised when a database change is unsafe or execution fails."""


@dataclass(frozen=True)
class DatabaseChangeConfig:
    connection_string: str
    statement_timeout_ms: int = 15000
    lock_timeout_ms: int = 5000

    @classmethod
    def from_env(cls, database: str | None = None) -> "DatabaseChangeConfig":
        load_dotenv()
        connection = os.environ.get("POSTGRES_DB_CONN_STRING") or os.environ.get("DATABASE_URL")
        if not connection:
            raise DatabaseChangeRepositoryError("POSTGRES_DB_CONN_STRING is required")
        return cls(
            connection_string=with_database_override(connection, database),
            statement_timeout_ms=int(os.environ.get("POSTGRES_STATEMENT_TIMEOUT", "15000")),
            lock_timeout_ms=int(os.environ.get("POSTGRES_LOCK_TIMEOUT", "5000")),
        )


class DatabaseChangeRepository:
    """Repository for controlled Postgres changes."""

    def __init__(self, config: DatabaseChangeConfig | None = None, database: str | None = None) -> None:
        self.config = config or DatabaseChangeConfig.from_env(database=database)

    @property
    def database(self) -> str | None:
        return connection_database(self.config.connection_string)

    def test_write_permissions(self, *, execute: bool = False) -> dict[str, Any]:
        sql = """
        begin;
        create temp table ai_devkit_permission_probe(id int primary key, value text);
        insert into ai_devkit_permission_probe(id, value) values (1, 'probe');
        update ai_devkit_permission_probe set value = 'updated' where id = 1;
        delete from ai_devkit_permission_probe where id = 1;
        rollback;
        """
        if not execute:
            return {
                "dry_run": True,
                "database": self.database,
                "checks": ["create_temp_table", "insert", "update", "delete"],
                "message": "Re-run with --execute to test permissions inside rollback.",
            }
        self._psql(wrap_with_timeouts(sql))
        return {"dry_run": False, "database": self.database, "write_permissions": True, "rolled_back": True}

    def plan_migration(self, *, path: str) -> dict[str, Any]:
        sql = read_sql_file(path)
        return {**plan_sql(sql, path=path), "database": self.database}

    def apply_migration(self, *, path: str, execute: bool = False, name: str | None = None) -> dict[str, Any]:
        plan = self.plan_migration(path=path)
        migration_id = migration_id_from_path(path)
        migration_name = name or Path(path).name
        if not execute:
            return {"dry_run": True, "database": self.database, "migration_id": migration_id, "plan": plan}
        if plan["destructive"] and not plan["rollback_path"]:
            raise DatabaseChangeRepositoryError("destructive migration requires a rollback .down.sql file")
        self.ensure_history_table()
        existing = self._query_json(
            f"select id, checksum, status from ai_devkit_migrations where id = {sql_literal(migration_id)}"
        )
        if existing:
            if existing[0].get("checksum") != plan["checksum"]:
                raise DatabaseChangeRepositoryError("migration already applied with different checksum")
            return {"dry_run": False, "database": self.database, "migration_id": migration_id, "already_applied": True}
        self._psql(wrap_in_transaction(read_sql_file(path), self.config))
        self.record_migration(
            migration_id=migration_id,
            name=migration_name,
            checksum=plan["checksum"],
            status="applied",
            rollback_available=bool(plan["rollback_path"]),
            metadata=plan,
        )
        return {"dry_run": False, "database": self.database, "migration_id": migration_id, "status": "applied", "plan": plan}

    def rollback_migration(self, *, path: str, execute: bool = False) -> dict[str, Any]:
        sql = read_sql_file(path)
        plan = plan_sql(sql, path=path)
        migration_id = migration_id_from_path(path.replace(".down.sql", ".up.sql"))
        if not execute:
            return {"dry_run": True, "database": self.database, "migration_id": migration_id, "plan": plan}
        self.ensure_history_table()
        self._psql(wrap_in_transaction(sql, self.config))
        self._psql(
            wrap_with_timeouts(
                f"update ai_devkit_migrations set status = 'rolled_back', metadata = metadata || '{{\"rolled_back\": true}}'::jsonb where id = {sql_literal(migration_id)};",
                self.config,
            )
        )
        return {"dry_run": False, "database": self.database, "migration_id": migration_id, "status": "rolled_back", "plan": plan}

    def run_write_script(self, *, path: str, execute: bool = False) -> dict[str, Any]:
        sql = read_sql_file(path)
        plan = plan_sql(sql, path=path)
        if not execute:
            return {"dry_run": True, "database": self.database, "plan": plan}
        if plan["blocked"]:
            raise DatabaseChangeRepositoryError("script contains blocked SQL")
        self._psql(wrap_in_transaction(sql, self.config))
        return {"dry_run": False, "database": self.database, "status": "executed", "plan": plan}

    def upsert_records(
        self,
        *,
        schema: str,
        table: str,
        key_column: str,
        input_path: str,
        execute: bool = False,
    ) -> dict[str, Any]:
        records = read_records(input_path)
        if not records:
            raise DatabaseChangeRepositoryError("input file contains no records")
        validate_identifier(schema, "schema")
        validate_identifier(table, "table")
        validate_identifier(key_column, "key_column")
        columns = list(records[0].keys())
        for column in columns:
            validate_identifier(column, "column")
        if key_column not in columns:
            raise DatabaseChangeRepositoryError("key_column must be present in input records")
        sql = build_upsert_sql(schema, table, key_column, records, columns)
        plan = plan_sql(sql, path=input_path)
        if not execute:
            return {"dry_run": True, "database": self.database, "record_count": len(records), "plan": plan}
        self._psql(wrap_in_transaction(sql, self.config))
        return {"dry_run": False, "database": self.database, "record_count": len(records), "status": "upserted", "plan": plan}

    def update_records(
        self,
        *,
        schema: str,
        table: str,
        set_json: dict[str, Any],
        where_sql: str,
        execute: bool = False,
    ) -> dict[str, Any]:
        validate_identifier(schema, "schema")
        validate_identifier(table, "table")
        validate_where_clause(where_sql)
        if not set_json:
            raise DatabaseChangeRepositoryError("set_json must contain at least one field")
        assignments = []
        for key, value in set_json.items():
            validate_identifier(key, "column")
            assignments.append(f"{quote_ident(key)} = {sql_literal(str(value))}")
        qualified = qualified_name(schema, table)
        count_sql = f"select count(*)::bigint as count from {qualified} where {where_sql}"
        affected = self._query_json(count_sql)[0]["count"] if execute else None
        sql = f"update {qualified} set {', '.join(assignments)} where {where_sql};"
        plan = plan_sql(sql, path=f"{schema}.{table}")
        if not execute:
            return {"dry_run": True, "database": self.database, "plan": plan, "where_sql": where_sql}
        self._psql(wrap_in_transaction(sql, self.config))
        return {"dry_run": False, "database": self.database, "affected_rows_before": affected, "status": "updated", "plan": plan}

    def migration_report(self) -> dict[str, Any]:
        self.ensure_history_table()
        rows = self._query_json(
            """
            select id, name, checksum, applied_at, applied_by, status, rollback_available
            from ai_devkit_migrations
            order by applied_at desc
            """
        )
        return {"database": self.database, "count": len(rows), "migrations": rows}

    def ensure_history_table(self) -> None:
        self._psql(
            wrap_with_timeouts(
                """
                create table if not exists ai_devkit_migrations (
                  id text primary key,
                  name text not null,
                  checksum text not null,
                  applied_at timestamptz not null default now(),
                  applied_by text not null,
                  status text not null,
                  rollback_available boolean not null,
                  metadata jsonb
                );
                """,
                self.config,
            )
        )

    def record_migration(
        self,
        *,
        migration_id: str,
        name: str,
        checksum: str,
        status: str,
        rollback_available: bool,
        metadata: dict[str, Any],
    ) -> None:
        self._psql(
            wrap_with_timeouts(
                f"""
                insert into ai_devkit_migrations
                  (id, name, checksum, applied_by, status, rollback_available, metadata)
                values
                  ({sql_literal(migration_id)}, {sql_literal(name)}, {sql_literal(checksum)}, current_user,
                   {sql_literal(status)}, {str(rollback_available).lower()}, {sql_literal(json.dumps(metadata))}::jsonb);
                """,
                self.config,
            )
        )

    def _query_json(self, query: str) -> list[dict[str, Any]]:
        sql = f"""
        {timeout_sql(self.config)}
        copy (
          select coalesce(json_agg(row_to_json(q)), '[]'::json)
          from ({query.strip().rstrip(';')}) q
        ) to stdout;
        """
        text = self._psql(sql).strip() or "[]"
        return json.loads(text)

    def _psql(self, sql: str) -> str:
        env = os.environ.copy()
        command = ["psql", "-X", "-q", "-t", "-A", "-v", "ON_ERROR_STOP=1", "-f", "-"]
        extra_env = connection_env(self.config.connection_string)
        if extra_env:
            env.update(extra_env)
        else:
            command.insert(1, self.config.connection_string)
        result = subprocess.run(command, input=sql, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        if result.returncode != 0:
            raise DatabaseChangeRepositoryError(result.stderr.strip() or "psql failed")
        return result.stdout


DANGEROUS_PATTERNS = [
    r"\bdrop\s+database\b",
    r"\bdrop\s+schema\b",
    r"\balter\s+system\b",
    r"\bcopy\b.+\bprogram\b",
    r"\bcreate\s+extension\b",
    r"\bgrant\b",
    r"\brevoke\b",
]

DESTRUCTIVE_PATTERNS = [
    r"\bdrop\s+table\b",
    r"\bdrop\s+column\b",
    r"\btruncate\b",
    r"\bdelete\s+from\b",
]


def plan_sql(sql: str, *, path: str | None = None) -> dict[str, Any]:
    normalized = strip_sql_comments(sql)
    statements = split_statements(normalized)
    blocked = any(re.search(pattern, normalized, re.I | re.S) for pattern in DANGEROUS_PATTERNS)
    destructive = any(re.search(pattern, normalized, re.I | re.S) for pattern in DESTRUCTIVE_PATTERNS)
    operations = classify_statements(statements)
    checksum = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    rollback_path = rollback_path_for(path) if path else None
    return {
        "path": path,
        "checksum": checksum,
        "statement_count": len(statements),
        "operations": operations,
        "blocked": blocked,
        "destructive": destructive,
        "transactional": not contains_non_transactional(normalized),
        "rollback_path": rollback_path,
        "requires_execute": True,
    }


def classify_statements(statements: list[str]) -> list[dict[str, str]]:
    operations = []
    for statement in statements:
        match = re.match(r"\s*([a-zA-Z]+)(?:\s+([a-zA-Z]+))?", statement)
        command = " ".join(part for part in (match.group(1), match.group(2) if match else None) if part).lower() if match else "unknown"
        operations.append({"command": command, "preview": statement.strip()[:180]})
    return operations


def contains_non_transactional(sql: str) -> bool:
    return bool(re.search(r"\b(create\s+index\s+concurrently|drop\s+index\s+concurrently|vacuum)\b", sql, re.I))


def wrap_in_transaction(sql: str, config: DatabaseChangeConfig) -> str:
    plan = plan_sql(sql)
    if plan["blocked"]:
        raise DatabaseChangeRepositoryError("SQL contains blocked operation")
    if plan["transactional"]:
        return f"{timeout_sql(config)}\nbegin;\n{sql.strip().rstrip(';')};\ncommit;\n"
    return wrap_with_timeouts(sql, config)


def wrap_with_timeouts(sql: str, config: DatabaseChangeConfig | None = None) -> str:
    return f"{timeout_sql(config)}\n{sql.strip()}\n"


def timeout_sql(config: DatabaseChangeConfig | None = None) -> str:
    statement_timeout = config.statement_timeout_ms if config else 15000
    lock_timeout = config.lock_timeout_ms if config else 5000
    return f"set statement_timeout = {int(statement_timeout)}; set lock_timeout = {int(lock_timeout)};"


def split_statements(sql: str) -> list[str]:
    return [item.strip() for item in sql.split(";") if item.strip()]


def strip_sql_comments(sql: str) -> str:
    without_line = re.sub(r"--.*?$", "", sql, flags=re.M)
    return re.sub(r"/\*.*?\*/", "", without_line, flags=re.S).strip()


def read_sql_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def migration_id_from_path(path: str) -> str:
    name = Path(path).name
    return re.sub(r"\.(up|down)\.sql$", "", name)


def rollback_path_for(path: str | None) -> str | None:
    if not path or not path.endswith(".up.sql"):
        return None
    candidate = Path(path[:-7] + ".down.sql")
    return str(candidate) if candidate.exists() else None


def read_records(path: str) -> list[dict[str, Any]]:
    file_path = Path(path)
    if file_path.suffix.lower() == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("records", [])
    if file_path.suffix.lower() == ".csv":
        with file_path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    raise DatabaseChangeRepositoryError("input must be .json or .csv")


def build_upsert_sql(schema: str, table: str, key_column: str, records: list[dict[str, Any]], columns: list[str]) -> str:
    qualified = qualified_name(schema, table)
    column_list = ", ".join(quote_ident(column) for column in columns)
    values = []
    for record in records:
        values.append("(" + ", ".join(sql_literal(str(record.get(column, ""))) for column in columns) + ")")
    updates = ", ".join(f"{quote_ident(column)} = excluded.{quote_ident(column)}" for column in columns if column != key_column)
    conflict_action = f"do update set {updates}" if updates else "do nothing"
    return f"insert into {qualified} ({column_list}) values {', '.join(values)} on conflict ({quote_ident(key_column)}) {conflict_action};"


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
        raise DatabaseChangeRepositoryError("database override requires a postgres connection URL")
    return urllib.parse.urlunparse(parsed._replace(path="/" + urllib.parse.quote(database, safe="")))


def validate_database_name(value: str) -> None:
    if not re.match(r"^[A-Za-z0-9_-]+$", value or ""):
        raise DatabaseChangeRepositoryError("invalid database name")


def validate_identifier(value: str, label: str) -> None:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", value or ""):
        raise DatabaseChangeRepositoryError(f"invalid {label} identifier")


def validate_where_clause(value: str) -> None:
    normalized = strip_sql_comments(value or "").strip()
    lowered = normalized.lower()
    if not normalized or lowered in {"true", "1=1"}:
        raise DatabaseChangeRepositoryError("where_sql must be specific")
    if ";" in normalized:
        raise DatabaseChangeRepositoryError("where_sql must be a single expression")
    blocked = [
        r"\binsert\b",
        r"\bupdate\b",
        r"\bdelete\b",
        r"\bdrop\b",
        r"\btruncate\b",
        r"\balter\b",
        r"\bcreate\b",
        r"\bgrant\b",
        r"\brevoke\b",
    ]
    if any(re.search(pattern, normalized, re.I) for pattern in blocked):
        raise DatabaseChangeRepositoryError("where_sql contains blocked keyword")


def quote_ident(value: str) -> str:
    validate_identifier(value, "identifier")
    return f'"{value}"'


def qualified_name(schema: str, table: str) -> str:
    return f"{quote_ident(schema)}.{quote_ident(table)}"


def sql_literal(value: str | None) -> str:
    if value is None:
        return "null"
    return "'" + str(value).replace("'", "''") + "'"


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
