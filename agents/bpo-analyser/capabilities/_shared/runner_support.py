#!/usr/bin/env python3
"""Shared helpers for BPO Analyser capability runners."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
BPO_DIR = AGENT_DIR / "infra" / "integrations" / "bpo"


def load_fixture(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_repository() -> Any:
    sys.path.insert(0, str(BPO_DIR))
    from bpo_repository import BpoRepository  # pylint: disable=import-error

    return BpoRepository()


def write_output(markdown: str, output: str | None) -> None:
    if output:
        Path(output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)


def write_payload(payload: dict[str, Any], renderer: Any, output: str | None, output_format: str) -> None:
    if output_format == "json":
        content = json.dumps(sanitize_output(payload), ensure_ascii=False, indent=2) + "\n"
    else:
        content = renderer(payload)
    write_output(content, output)


def sanitize_output(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {item_key: sanitize_output(item_value, item_key) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [sanitize_output(item) for item in value]
    normalized_key = (key or "").lower()
    if normalized_key == "cpf":
        return mask_cpf(str(value))
    if normalized_key in {"file_base64", "base64", "content_base64"} and value:
        return "[redacted]"
    return value


def print_error(exc: Exception) -> int:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1


def value_or_dash(value: Any) -> str:
    if value is None or value == "":
        return "-"
    return str(value)


def bool_label(value: Any) -> str:
    if value is True:
        return "sim"
    if value is False:
        return "nao"
    return "-"


def yes_no(value: Any) -> str:
    if value is True:
        return "True"
    if value is False:
        return "False"
    return value_or_dash(value)


def mask_cpf(value: str | None) -> str:
    if "***" in str(value or ""):
        return str(value)
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) != 11:
        return "-"
    return f"{digits[:3]}.***.***-{digits[-2:]}"


def proposal_lines(proposal: dict[str, Any]) -> list[str]:
    processing = proposal.get("processing_status") or {}
    amounts = proposal.get("amounts") or {}
    return [
        f"- Proposta: {value_or_dash(proposal.get('proposal_number'))}",
        f"- Contrato: {value_or_dash(proposal.get('contract_number'))}",
        f"- Formalizacao: {value_or_dash(proposal.get('formalization_id'))}",
        f"- Status processamento: {bool_label(processing.get('status'))}",
        f"- Erro processamento: {value_or_dash(processing.get('error_message'))}",
        f"- Situacao: {value_or_dash(proposal.get('situation'))}",
        f"- Atividade: {value_or_dash(proposal.get('activity'))}",
        f"- Data situacao: {value_or_dash(proposal.get('situation_date'))}",
        f"- Cliente: {value_or_dash(proposal.get('customer_name'))}",
        f"- CPF: {mask_cpf(proposal.get('cpf'))}",
        f"- Produto: {value_or_dash(proposal.get('product_name'))}",
        f"- Tipo proposta: {value_or_dash(proposal.get('proposal_type'))}",
        f"- Valor solicitado: {value_or_dash(amounts.get('requested'))}",
        f"- Valor liberado: {value_or_dash(amounts.get('released'))}",
    ]


def render_observations(observations: list[dict[str, Any]]) -> list[str]:
    if not observations:
        return ["- Nenhuma observacao retornada."]
    lines = []
    for item in observations:
        lines.append(
            f"- {value_or_dash(item.get('date'))}: {value_or_dash(item.get('text'))}"
        )
    return lines


def render_documents_table(files: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Proposta | Arquivo | Tipo | Extensao | Tamanho | Conteudo |",
        "|---|---|---|---|---:|---|",
    ]
    if not files:
        lines.append("| - | Nenhum documento retornado | - | - | - | - |")
        return lines
    for item in files:
        lines.append(
            "| "
            + " | ".join(
                [
                    value_or_dash(item.get("proposal_number")),
                    value_or_dash(item.get("file_name")),
                    value_or_dash(item.get("document_type")),
                    value_or_dash(item.get("extension_file_type")),
                    value_or_dash(item.get("size")),
                    "base64 presente" if item.get("has_file_base64") else "-",
                ]
            )
            + " |"
        )
    return lines


def render_proposals_table(proposals: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Proposta | Situacao | Tipo | Elegivel | Ultimo vencimento | Limite saque | Valor liberado | Orgao |",
        "|---|---|---|---|---|---:|---:|---|",
    ]
    if not proposals:
        lines.append("| - | Nenhuma proposta retornada | - | - | - | - | - | - |")
        return lines
    for item in proposals:
        lines.append(
            "| "
            + " | ".join(
                [
                    value_or_dash(item.get("proposal_number")),
                    value_or_dash(item.get("situation")),
                    value_or_dash(item.get("proposal_type")),
                    bool_label(item.get("is_eligible")),
                    value_or_dash(item.get("last_due_date")),
                    value_or_dash(item.get("withdraw_limit")),
                    value_or_dash(item.get("released_amount")),
                    value_or_dash(item.get("agency") or item.get("employer")),
                ]
            )
            + " |"
        )
    return lines


def proposal_by_cpf_lines(proposal: dict[str, Any] | None) -> list[str]:
    if not proposal:
        return ["- Nenhuma proposta selecionada."]
    customer = proposal.get("customer") or {}
    return [
        f"- Proposta: {value_or_dash(proposal.get('proposal_number'))}",
        f"- Situacao: {value_or_dash(proposal.get('situation'))}",
        f"- Tipo: {value_or_dash(proposal.get('proposal_type'))}",
        f"- Elegivel: {bool_label(proposal.get('is_eligible'))}",
        f"- Atividade: {value_or_dash(proposal.get('activity'))}",
        f"- Cliente: {value_or_dash(customer.get('name'))}",
        f"- CPF: {mask_cpf(customer.get('cpf'))}",
        f"- Matricula: {value_or_dash(customer.get('registration'))}",
        f"- Orgao/empregador: {value_or_dash(proposal.get('agency') or proposal.get('employer'))}",
        f"- Data ultimo vencimento: {value_or_dash(proposal.get('last_due_date'))}",
        f"- Limite saque: {value_or_dash(proposal.get('withdraw_limit'))}",
        f"- Valor liberado: {value_or_dash(proposal.get('released_amount'))}",
    ]
