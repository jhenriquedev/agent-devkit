#!/usr/bin/env python3
"""Markdown report renderers for data-scientist capabilities."""

from __future__ import annotations

from typing import Any


def render_data_report(payload: dict[str, Any]) -> str:
    dataset = payload["dataset"]
    quality = payload["quality"]
    sensitive = payload["sensitive_data"]
    lines = [
        "# Relatorio de Dados",
        "",
        "## Fonte",
        "",
        f"- Arquivo: {dataset['name']}",
        f"- Formato: {dataset['format']}",
        f"- Linhas: {dataset['row_count']}",
        f"- Linhas originais: {dataset.get('original_row_count', dataset['row_count'])}",
        f"- Truncado/amostrado: {'sim' if dataset.get('truncated') else 'nao'}",
        f"- Colunas: {dataset['column_count']}",
        f"- SHA-256: {dataset['sha256']}",
        f"- Warnings de leitura: {', '.join(dataset.get('warnings', [])) or 'nenhum'}",
        "",
        "## Qualidade",
        "",
        f"- Score: {quality['quality_score']}",
        f"- Linhas duplicadas: {quality['duplicate_row_count']}",
        f"- Linhas vazias: {quality['empty_row_count']}",
        f"- Colunas com nulos: {', '.join(quality['columns_with_missing_values']) or 'nenhuma'}",
        "",
        "## Dados sensiveis",
        "",
        f"- Possui dados sensiveis: {'sim' if sensitive['has_sensitive_data'] else 'nao'}",
    ]
    for column, kinds in sensitive["columns"].items():
        lines.append(f"- {column}: {', '.join(kinds)}")
    lines.extend(["", "## Colunas", ""])
    for column, details in payload["columns"].items():
        lines.append(
            f"- {column}: tipo={details['inferred_type']}, nulos={details['missing_count']}, unicos={details['unique_count']}"
        )
    lines.extend(
        [
            "",
            "## Reprodutibilidade",
            "",
            f"- Dataset hash: {dataset['sha256']}",
            "- Fonte nao e alterada pela capability.",
            "- Reexecute o mesmo comando com os mesmos controles de leitura para reproduzir o perfil.",
            "",
            "## Limitacoes",
            "",
            "- Inferencia de tipos e qualidade e baseline e depende dos dados carregados.",
            "- Analises sobre amostra truncada devem ser tratadas como indicativas.",
            "- Deteccao de dados sensiveis usa heuristicas e pode gerar falso positivo ou falso negativo.",
            "",
            "## Base para PDF",
            "",
            "- Este markdown e o formato canonico para conversao posterior em PDF.",
            "- Preserve as secoes Fonte, Qualidade, Dados sensiveis, Colunas, Reprodutibilidade e Limitacoes na exportacao.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_reconciliation_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Relatorio de Conciliacao",
        "",
        "## Resumo",
        "",
        f"- Conciliados: {summary['matched_count']}",
        f"- Divergentes: {summary['mismatched_count']}",
        f"- Ausentes na direita: {summary['missing_right_count']}",
        f"- Ausentes na esquerda: {summary['missing_left_count']}",
        f"- Chaves duplicadas: {summary['duplicate_key_count']}",
        "",
        "## Regras",
        "",
        f"- Chave: {', '.join(payload['rules']['key'])}",
        f"- Colunas comparadas: {', '.join(payload['rules']['compare_columns'])}",
        f"- Tolerancia numerica: {payload['rules']['numeric_tolerance']}",
    ]
    if payload["mismatched"]:
        lines.extend(["", "## Divergencias", ""])
        for item in payload["mismatched"][:20]:
            lines.append(f"- Chave {item['key']}:")
            for diff in item["differences"]:
                lines.append(f"  - {diff['column']}: {diff['left']} != {diff['right']} ({diff['reason']})")
    return "\n".join(lines) + "\n"
