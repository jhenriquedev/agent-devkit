#!/usr/bin/env python3
"""Controlled SQL Server change repository backed by pyodbc."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class SqlServerChangeRepositoryError(RuntimeError):
    """Raised when a SQL Server change is unsafe or execution fails."""


DANGEROUS_PATTERNS = [
    r"\bdrop\s+database\b",
    r"\balter\s+server\b",
    r"\balter\s+login\b",
    r"\bcreate\s+login\b",
    r"\bgrant\b",
    r"\brevoke\b",
    r"\bbackup\s+database\b",
    r"\brestore\b",
    r"\btruncate\b",
    r"\bxp_cmdshell\b",
    r"\bsp_configure\b",
    r"\bopenrowset\b",
    r"\blinked\s+server\b",
]

DESTRUCTIVE_PATTERNS = [
    r"\bdrop\s+table\b",
    r"\bdrop\s+column\b",
    r"\bdelete\s+from\b",
]

NON_TRANSACTIONAL_PATTERNS = [
    r"\bbackup\b",
    r"\brestore\b",
    r"\balter\s+database\b",
]


@dataclass(frozen=True)
class SqlServerChangeConfig:
    connection_string: str
    statement_timeout_ms: int = 15000
    lock_timeout_ms: int = 5000
    max_affected_rows: int = 100
    change_schema: str = "ai_devkit"

    @classmethod
    def from_env(cls, database: str | None = None) -> "SqlServerChangeConfig":
        load_dotenv()
        connection = os.environ.get("SQLSERVER_DB_CONN_STRING") or os.environ.get("MSSQL_DB_CONN_STRING")
        if not connection:
            raise SqlServerChangeRepositoryError("SQLSERVER_DB_CONN_STRING is required")
        return cls(
            connection_string=with_database_override(connection, database),
            statement_timeout_ms=int(os.environ.get("SQLSERVER_STATEMENT_TIMEOUT", "15000")),
            lock_timeout_ms=int(os.environ.get("SQLSERVER_LOCK_TIMEOUT", "5000")),
            max_affected_rows=int(os.environ.get("SQLSERVER_MAX_AFFECTED_ROWS", "100")),
            change_schema=os.environ.get("SQLSERVER_CHANGE_SCHEMA", "ai_devkit"),
        )


class SqlServerChangeRepository:
    """Repository for controlled SQL Server changes."""

    def __init__(self, config: SqlServerChangeConfig | None = None, database: str | None = None) -> None:
        self.config = config or SqlServerChangeConfig.from_env(database=database)

    def test_write_permissions(self, *, execute: bool = False) -> dict[str, Any]:
        sql = """
        set xact_abort on;
        begin transaction;
        create table #ai_devkit_permission_probe(id int primary key, value nvarchar(100));
        insert into #ai_devkit_permission_probe(id, value) values (1, N'probe');
        update #ai_devkit_permission_probe set value = N'updated' where id = 1;
        delete from #ai_devkit_permission_probe where id = 1;
        rollback transaction;
        """
        if not execute:
            return {
                "dry_run": True,
                "checks": ["create_temp_table", "insert", "update", "delete"],
                "message": "Re-run with --execute to test permissions inside rollback.",
            }
        self._execute_sql(wrap_with_safety(sql, self.config))
        return {"dry_run": False, "write_permissions": True, "rolled_back": True}

    def plan_migration(self, *, path: str) -> dict[str, Any]:
        return {**plan_sql(read_sql_file(path), path=path), "change_schema": self.config.change_schema}

    def apply_migration(
        self,
        *,
        path: str,
        rollback_path: str | None = None,
        execute: bool = False,
        name: str | None = None,
    ) -> dict[str, Any]:
        plan = self.plan_migration(path=path)
        if rollback_path:
            plan["rollback_path"] = rollback_path
        migration_id = migration_id_from_path(path)
        if not execute:
            return {"dry_run": True, "migration_id": migration_id, "plan": plan}
        if plan["blocked"]:
            raise SqlServerChangeRepositoryError("migration contains blocked SQL")
        if plan["destructive"] and not plan.get("rollback_path"):
            raise SqlServerChangeRepositoryError("destructive migration requires rollback_path")
        self.ensure_control_tables()
        existing = self._query_rows(
            f"select migration_id, checksum, status from {control_table(self.config, 'schema_migrations')} where migration_id = {sql_literal(migration_id)}"
        )
        if existing:
            if existing[0].get("checksum") != plan["checksum"]:
                raise SqlServerChangeRepositoryError("migration already applied with different checksum")
            return {"dry_run": False, "migration_id": migration_id, "already_applied": True}
        self._execute_sql(wrap_in_transaction(read_sql_file(path), self.config))
        self.record_change(
            operation_type="migration",
            name=name or Path(path).name,
            checksum=plan["checksum"],
            status="applied",
            affected_rows=None,
            metadata={**plan, "migration_id": migration_id},
        )
        self._execute_sql(
            wrap_with_safety(
                f"insert into {control_table(self.config, 'schema_migrations')} (migration_id, name, checksum, status) values ({sql_literal(migration_id)}, {sql_literal(name or Path(path).name)}, {sql_literal(plan['checksum'])}, N'applied');",
                self.config,
            )
        )
        return {"dry_run": False, "migration_id": migration_id, "status": "applied", "plan": plan}

    def rollback_migration(self, *, path: str, execute: bool = False) -> dict[str, Any]:
        plan = plan_sql(read_sql_file(path), path=path)
        migration_id = migration_id_from_path(path.replace(".down.sql", ".up.sql"))
        if not execute:
            return {"dry_run": True, "migration_id": migration_id, "plan": plan}
        if plan["blocked"]:
            raise SqlServerChangeRepositoryError("rollback contains blocked SQL")
        self.ensure_control_tables()
        self._execute_sql(wrap_in_transaction(read_sql_file(path), self.config))
        self.record_change(
            operation_type="rollback",
            name=Path(path).name,
            checksum=plan["checksum"],
            status="rolled_back",
            affected_rows=None,
            metadata={**plan, "migration_id": migration_id},
        )
        return {"dry_run": False, "migration_id": migration_id, "status": "rolled_back", "plan": plan}

    def run_write_script(self, *, path: str, execute: bool = False) -> dict[str, Any]:
        sql = read_sql_file(path)
        plan = plan_sql(sql, path=path)
        if not execute:
            return {"dry_run": True, "plan": plan}
        if plan["blocked"]:
            raise SqlServerChangeRepositoryError("script contains blocked SQL")
        self._execute_sql(wrap_in_transaction(sql, self.config))
        return {"dry_run": False, "status": "executed", "plan": plan}

    def create_object(self, *, path: str, execute: bool = False) -> dict[str, Any]:
        sql = read_sql_file(path)
        plan = plan_sql(sql, path=path)
        if not any(op["command"].startswith("create") for op in plan["operations"]):
            raise SqlServerChangeRepositoryError("create-object requires CREATE statement")
        if not execute:
            return {"dry_run": True, "plan": plan}
        if plan["blocked"]:
            raise SqlServerChangeRepositoryError("script contains blocked SQL")
        self._execute_sql(wrap_in_transaction(sql, self.config))
        return {"dry_run": False, "status": "created", "plan": plan}

    def update_records(
        self,
        *,
        schema: str,
        table: str,
        set_json: dict[str, Any],
        where_sql: str,
        execute: bool = False,
        max_affected_rows: int | None = None,
    ) -> dict[str, Any]:
        validate_identifier(schema, "schema")
        validate_identifier(table, "table")
        validate_where_clause(where_sql)
        if not set_json:
            raise SqlServerChangeRepositoryError("set_json must contain at least one field")
        max_rows = max_affected_rows or self.config.max_affected_rows
        assignments = []
        for key, value in set_json.items():
            validate_identifier(key, "column")
            assignments.append(f"{quote_ident(key)} = {sql_literal(value)}")
        qualified = qualified_name(schema, table)
        sql = f"update {qualified} set {', '.join(assignments)} where {where_sql};"
        plan = plan_sql(sql, path=f"{schema}.{table}")
        if not execute:
            return {"dry_run": True, "where_sql": where_sql, "max_affected_rows": max_rows, "plan": plan}
        affected = self.count_where(schema=schema, table=table, where_sql=where_sql)
        enforce_affected_limit(affected, max_rows)
        self._execute_sql(wrap_in_transaction(sql, self.config))
        self.record_change("update", f"{schema}.{table}", plan["checksum"], "updated", affected, plan)
        return {"dry_run": False, "affected_rows": affected, "status": "updated", "plan": plan}

    def delete_records(
        self,
        *,
        schema: str,
        table: str,
        where_sql: str,
        execute: bool = False,
        confirm_delete: bool = False,
        max_affected_rows: int | None = None,
    ) -> dict[str, Any]:
        validate_identifier(schema, "schema")
        validate_identifier(table, "table")
        validate_where_clause(where_sql)
        max_rows = max_affected_rows or self.config.max_affected_rows
        sql = f"delete from {qualified_name(schema, table)} where {where_sql};"
        plan = plan_sql(sql, path=f"{schema}.{table}")
        if not execute:
            return {"dry_run": True, "where_sql": where_sql, "max_affected_rows": max_rows, "plan": plan}
        if not confirm_delete:
            raise SqlServerChangeRepositoryError("--confirm-delete is required")
        affected = self.count_where(schema=schema, table=table, where_sql=where_sql)
        enforce_affected_limit(affected, max_rows)
        self._execute_sql(wrap_in_transaction(sql, self.config))
        self.record_change("delete", f"{schema}.{table}", plan["checksum"], "deleted", affected, plan)
        return {"dry_run": False, "affected_rows": affected, "status": "deleted", "plan": plan}

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
            raise SqlServerChangeRepositoryError("input file contains no records")
        sql = build_upsert_sql(schema, table, key_column, records)
        plan = plan_sql(sql, path=input_path)
        if not execute:
            return {"dry_run": True, "record_count": len(records), "plan": plan}
        self._execute_sql(wrap_in_transaction(sql, self.config))
        self.record_change("upsert", f"{schema}.{table}", plan["checksum"], "upserted", len(records), plan)
        return {"dry_run": False, "record_count": len(records), "status": "upserted", "plan": plan}

    def backup_records(self, *, schema: str, table: str, where_sql: str, execute: bool = False) -> dict[str, Any]:
        validate_where_clause(where_sql)
        validate_identifier(schema, "schema")
        validate_identifier(table, "table")
        if not execute:
            return {"dry_run": True, "schema": schema, "table": table, "where_sql": where_sql}
        self.ensure_control_tables()
        source = qualified_name(schema, table)
        backup_table = control_table(self.config, "record_backups")
        sql = f"""
        insert into {backup_table} (source_table, where_sql, payload_json, backed_up_at)
        select {sql_literal(source)}, {sql_literal(where_sql)},
               (select * from {source} where {where_sql} for json path),
               sysdatetime();
        """
        self._execute_sql(wrap_in_transaction(sql, self.config))
        return {"dry_run": False, "schema": schema, "table": table, "status": "backed_up"}

    def change_report(self) -> dict[str, Any]:
        self.ensure_control_tables()
        rows = self._query_rows(
            f"""
            select top (100)
              id, operation_type, name, checksum, status, affected_rows, executed_at, executed_by
            from {control_table(self.config, 'change_audit')}
            order by executed_at desc
            """
        )
        return {"count": len(rows), "changes": rows}

    def count_where(self, *, schema: str, table: str, where_sql: str) -> int:
        rows = self._query_rows(f"select count_big(*) as count from {qualified_name(schema, table)} where {where_sql}")
        return int(rows[0]["count"]) if rows else 0

    def ensure_control_tables(self) -> None:
        schema = quote_ident(self.config.change_schema)
        self._execute_sql(
            wrap_with_safety(
                f"""
                if schema_id(N{sql_literal_content(self.config.change_schema)}) is null
                  exec(N'create schema {schema}');

                if object_id(N'{self.config.change_schema}.change_audit', N'U') is null
                  create table {control_table(self.config, 'change_audit')} (
                    id bigint identity(1,1) primary key,
                    operation_type nvarchar(100) not null,
                    name nvarchar(255) not null,
                    checksum char(64) not null,
                    status nvarchar(100) not null,
                    affected_rows bigint null,
                    executed_at datetime2 not null default sysdatetime(),
                    executed_by sysname not null default suser_sname(),
                    metadata_json nvarchar(max) null
                  );

                if object_id(N'{self.config.change_schema}.record_backups', N'U') is null
                  create table {control_table(self.config, 'record_backups')} (
                    id bigint identity(1,1) primary key,
                    source_table nvarchar(512) not null,
                    where_sql nvarchar(max) not null,
                    payload_json nvarchar(max) null,
                    backed_up_at datetime2 not null default sysdatetime()
                  );

                if object_id(N'{self.config.change_schema}.schema_migrations', N'U') is null
                  create table {control_table(self.config, 'schema_migrations')} (
                    id bigint identity(1,1) primary key,
                    migration_id nvarchar(255) not null unique,
                    name nvarchar(255) not null,
                    checksum char(64) not null,
                    status nvarchar(100) not null,
                    executed_at datetime2 not null default sysdatetime(),
                    executed_by sysname not null default suser_sname()
                  );
                """,
                self.config,
            )
        )

    def record_change(
        self,
        operation_type: str,
        name: str,
        checksum: str,
        status: str,
        affected_rows: int | None,
        metadata: dict[str, Any],
    ) -> None:
        self.ensure_control_tables()
        sql = f"""
        insert into {control_table(self.config, 'change_audit')}
          (operation_type, name, checksum, status, affected_rows, metadata_json)
        values
          ({sql_literal(operation_type)}, {sql_literal(name)}, {sql_literal(checksum)},
           {sql_literal(status)}, {affected_rows if affected_rows is not None else 'null'},
           {sql_literal(json.dumps(metadata, ensure_ascii=False))});
        """
        self._execute_sql(wrap_with_safety(sql, self.config))

    def _query_rows(self, query: str) -> list[dict[str, Any]]:
        try:
            import pyodbc  # type: ignore
        except ImportError as exc:
            raise SqlServerChangeRepositoryError("pyodbc is required for real SQL Server calls") from exc
        try:
            with pyodbc.connect(self.config.connection_string, timeout=max(1, self.config.statement_timeout_ms // 1000)) as conn:
                cursor = conn.cursor()
                cursor.execute(f"set lock_timeout {int(self.config.lock_timeout_ms)}")
                cursor.execute(query)
                columns = [column[0] for column in cursor.description or []]
                return [dict(zip(columns, row)) for row in cursor.fetchall()] if columns else []
        except Exception as exc:
            raise SqlServerChangeRepositoryError(str(exc)) from exc

    def _execute_sql(self, sql: str) -> None:
        try:
            import pyodbc  # type: ignore
        except ImportError as exc:
            raise SqlServerChangeRepositoryError("pyodbc is required for real SQL Server calls") from exc
        try:
            with pyodbc.connect(self.config.connection_string, timeout=max(1, self.config.statement_timeout_ms // 1000)) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                conn.commit()
        except Exception as exc:
            raise SqlServerChangeRepositoryError(str(exc)) from exc


def plan_sql(sql: str, *, path: str | None = None) -> dict[str, Any]:
    normalized = strip_sql_comments(sql)
    statements = split_statements(normalized)
    blocked = any(re.search(pattern, normalized, re.I | re.S) for pattern in DANGEROUS_PATTERNS)
    destructive = any(re.search(pattern, normalized, re.I | re.S) for pattern in DESTRUCTIVE_PATTERNS)
    transactional = not any(re.search(pattern, normalized, re.I | re.S) for pattern in NON_TRANSACTIONAL_PATTERNS)
    operations = classify_statements(statements)
    checksum = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    rollback_path = rollback_path_for(path) if path else None
    risk_level = "blocked" if blocked else "high" if destructive else "medium" if operations else "low"
    return {
        "path": path,
        "checksum": checksum,
        "statement_count": len(statements),
        "operations": operations,
        "blocked": blocked,
        "destructive": destructive,
        "transactional": transactional,
        "rollback_path": rollback_path,
        "requires_execute": True,
        "risk_level": risk_level,
    }


def classify_statements(statements: list[str]) -> list[dict[str, str]]:
    operations = []
    for statement in statements:
        match = re.match(r"\s*([a-zA-Z]+)(?:\s+([a-zA-Z]+))?", statement)
        command = " ".join(part for part in (match.group(1), match.group(2) if match else None) if part).lower() if match else "unknown"
        operations.append({"command": command, "preview": statement.strip()[:180]})
    return operations


def validate_where_clause(where_sql: str) -> None:
    text = (where_sql or "").strip().rstrip(";")
    lowered = text.lower()
    if not text:
        raise SqlServerChangeRepositoryError("where clause is required")
    if lowered in {"1=1", "1 = 1", "true", "(1=1)", "(1 = 1)"}:
        raise SqlServerChangeRepositoryError("broad where clause is not allowed")
    if any(re.search(pattern, lowered, re.I) for pattern in DANGEROUS_PATTERNS):
        raise SqlServerChangeRepositoryError("where clause contains blocked SQL")
    if re.search(r"\b(insert|update|delete|drop|alter|truncate|merge|exec|execute)\b", lowered):
        raise SqlServerChangeRepositoryError("where clause contains blocked SQL keyword")


def enforce_affected_limit(affected: int, max_rows: int) -> None:
    if affected > max_rows:
        raise SqlServerChangeRepositoryError(f"affected rows {affected} exceeds max_affected_rows {max_rows}")


def wrap_in_transaction(sql: str, config: SqlServerChangeConfig) -> str:
    plan = plan_sql(sql)
    if plan["blocked"]:
        raise SqlServerChangeRepositoryError("SQL contains blocked operation")
    if plan["transactional"]:
        return f"{safety_sql(config)}\nbegin transaction;\n{sql.strip().rstrip(';')};\ncommit transaction;\n"
    return wrap_with_safety(sql, config)


def wrap_with_safety(sql: str, config: SqlServerChangeConfig | None = None) -> str:
    return f"{safety_sql(config)}\n{sql.strip()}\n"


def safety_sql(config: SqlServerChangeConfig | None = None) -> str:
    lock_timeout = config.lock_timeout_ms if config else 5000
    return f"set xact_abort on; set lock_timeout {int(lock_timeout)};"


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
    with file_path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def build_upsert_sql(schema: str, table: str, key_column: str, records: list[dict[str, Any]]) -> str:
    validate_identifier(schema, "schema")
    validate_identifier(table, "table")
    validate_identifier(key_column, "key_column")
    columns = list(records[0].keys())
    for column in columns:
        validate_identifier(column, "column")
    if key_column not in columns:
        raise SqlServerChangeRepositoryError("key_column must be present in input records")
    qualified = qualified_name(schema, table)
    statements = []
    for record in records:
        assignments = ", ".join(f"{quote_ident(column)} = {sql_literal(record.get(column))}" for column in columns if column != key_column)
        insert_columns = ", ".join(quote_ident(column) for column in columns)
        insert_values = ", ".join(sql_literal(record.get(column)) for column in columns)
        key_predicate = f"{quote_ident(key_column)} = {sql_literal(record.get(key_column))}"
        statements.append(
            f"""
            if exists (select 1 from {qualified} where {key_predicate})
              update {qualified} set {assignments} where {key_predicate}
            else
              insert into {qualified} ({insert_columns}) values ({insert_values})
            """
        )
    return ";\n".join(statements) + ";"


def validate_identifier(value: str, label: str) -> None:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_@$#]*$", value or ""):
        raise SqlServerChangeRepositoryError(f"invalid {label} identifier")


def quote_ident(value: str) -> str:
    validate_identifier(value, "identifier")
    return "[" + value.replace("]", "]]") + "]"


def qualified_name(schema: str, table: str) -> str:
    return f"{quote_ident(schema)}.{quote_ident(table)}"


def control_table(config: SqlServerChangeConfig, table: str) -> str:
    return qualified_name(config.change_schema, table)


def sql_literal(value: Any) -> str:
    if value is None:
        return "null"
    return "N'" + str(value).replace("'", "''") + "'"


def sql_literal_content(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


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


def validate_database_name(value: str) -> None:
    if not re.match(r"^[A-Za-z0-9_.-]+$", value or ""):
        raise SqlServerChangeRepositoryError("invalid database name")


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
