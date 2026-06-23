#!/usr/bin/env python3
"""Shared helpers for Postgres Data Analyzer runners."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
POSTGRES_DIR = AGENT_DIR / "infra" / "integrations" / "postgres"


def load_fixture(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_repository(database: str | None = None) -> Any:
    sys.path.insert(0, str(POSTGRES_DIR))
    from postgres_repository import PostgresRepository  # pylint: disable=import-error

    return PostgresRepository(database=database)


def validate_query_offline(query: str, limit: int) -> dict[str, Any]:
    sys.path.insert(0, str(POSTGRES_DIR))
    from postgres_repository import enforce_limit, validate_readonly_query  # pylint: disable=import-error

    safe_query = enforce_limit(validate_readonly_query(query), limit)
    return {"valid": True, "query": safe_query, "limit": limit}


def write_output(markdown: str, output: str | None) -> None:
    if output:
        Path(output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)


def print_error(exc: Exception) -> int:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1


def value_or_dash(value: Any) -> str:
    if value is None:
        return "-"
    text = " ".join(str(value).replace("\r", " ").replace("\n", " ").split())
    return text if text else "-"


def database_line(payload: dict[str, Any], requested_database: str | None = None) -> str:
    return f"- Database: {value_or_dash(payload.get('database') or requested_database)}"


def render_table(rows: list[dict[str, Any]], columns: list[str] | None = None, limit: int = 20) -> list[str]:
    if not rows:
        return ["| - |", "|---|", "| No rows. |"]
    selected = columns or list(rows[0].keys())
    lines = ["| " + " | ".join(selected) + " |", "|" + "|".join("---" for _ in selected) + "|"]
    for row in rows[:limit]:
        lines.append("| " + " | ".join(mask_if_sensitive(key, row.get(key)) for key in selected) + " |")
    return lines


def sensitive_kind_for_column(column: str) -> str | None:
    """Return the PII kind for a column name, or None if not sensitive."""
    lowered = column.lower()
    if "cpf" in lowered:
        return "cpf"
    if "cnpj" in lowered:
        return "cnpj"
    if "document" in lowered or "documento" in lowered:
        return "document"
    if "email" in lowered or "e_mail" in lowered:
        return "email"
    if "phone" in lowered or "telefone" in lowered or "celular" in lowered or "fone" in lowered:
        return "phone"
    if "password" in lowered or "senha" in lowered or "passwd" in lowered or "pwd" in lowered:
        return "password"
    if "token" in lowered or "secret" in lowered or "api_key" in lowered or "apikey" in lowered:
        return "token"
    if "address" in lowered or "endereco" in lowered or "logradouro" in lowered:
        return "address"
    # Metadata/structural columns that happen to end in _name are NOT person PII
    _metadata_name_cols = {
        "table_name", "column_name", "schema_name", "constraint_name",
        "index_name", "indexname", "database_name", "datname",
        "relationship_name", "owner_name", "sequence_name", "type_name",
        "role_name", "user_name",
    }
    if lowered in _metadata_name_cols:
        return None
    if (
        lowered in ("name", "nome", "full_name", "fullname", "first_name", "last_name",
                    "firstname", "lastname", "sobrenome", "razao_social")
        or "customer_name" in lowered
        or "client_name" in lowered
        or "person_name" in lowered
        or "pessoa_nome" in lowered
    ):
        return "name"
    return None


# Kinds always masked in human-readable row output
_ALWAYS_MASK_KINDS = {"cpf", "cnpj", "document"}
# Kinds masked/omitted when feasible (redacted marker shown)
_MASK_WHEN_FEASIBLE_KINDS = {"email", "phone", "name", "address", "token", "password"}


def mask_if_sensitive(column: str, value: Any) -> str:
    text = value_or_dash(value)
    kind = sensitive_kind_for_column(column)
    if kind is None:
        return text
    if kind == "cpf":
        return mask_cpf(text)
    if kind == "cnpj":
        return mask_cnpj(text)
    if kind in _ALWAYS_MASK_KINDS:
        return mask_cpf(text)  # fallback for generic document
    if kind in _MASK_WHEN_FEASIBLE_KINDS:
        return mask_generic_pii(text, kind)
    return text


def mask_cpf(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 11:
        return value
    return f"{digits[:3]}.***.***-{digits[-2:]}"


def mask_cnpj(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 14:
        return value
    return f"{digits[:2]}.***.***/****-{digits[-2:]}"


def mask_generic_pii(value: str, kind: str) -> str:
    """Redact a PII value, keeping a short hint of the kind."""
    if value == "-":
        return value
    return f"[{kind.upper()} REDACTED]"


def render_key_values(payload: dict[str, Any], keys: list[str]) -> list[str]:
    return [f"- {key}: {value_or_dash(payload.get(key))}" for key in keys]


def render_generic_table(rows: list[dict[str, Any]], limit: int = 30) -> list[str]:
    return render_table(rows, limit=limit)


def render_erd(relationships: list[dict[str, Any]]) -> list[str]:
    lines = ["```mermaid", "erDiagram"]
    if not relationships:
        lines.append('  EMPTY["No relationships detected"]')
    for row in relationships:
        parent = sanitize_mermaid(row.get("parent_table"))
        referenced = sanitize_mermaid(row.get("referenced_table"))
        lines.append(f"  {parent} }}o--|| {referenced} : {value_or_dash(row.get('relationship_name'))}")
    lines.append("```")
    return lines


def sanitize_mermaid(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", str(value or "unknown"))


def infer_domain(table_name: str) -> str:
    lowered = table_name.lower()
    groups = {
        "customer": ["customer", "client", "cliente", "person", "pessoa"],
        "sales": ["order", "pedido", "sale", "invoice", "fatura"],
        "finance": ["payment", "pagamento", "ledger", "account"],
        "audit": ["log", "audit", "history", "evento"],
        "security": ["user", "role", "permission", "auth"],
    }
    for domain, terms in groups.items():
        if any(term in lowered for term in terms):
            return domain
    return "other"
