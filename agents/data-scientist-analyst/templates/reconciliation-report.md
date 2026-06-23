# Relatorio de Conciliacao

> Contrato de saida de `generate-reconciliation-report`. A geracao real e feita
> por `reporting.py:render_reconciliation_report()`. Este arquivo documenta o
> formato fixo.

## Resumo Executivo

- Conciliados: {summary.matched_count}
- Divergentes: {summary.mismatched_count}
- Ausentes na direita: {summary.missing_right_count}
- Ausentes na esquerda: {summary.missing_left_count}
- Chaves duplicadas: {summary.duplicate_key_count}

## Regras de Conciliacao

- Chave: {rules.key | lista}
- Colunas comparadas: {rules.compare_columns | lista}
- Tolerancia numerica: {rules.numeric_tolerance}

## Fontes

- Esquerda: {fonte_esquerda} — SHA-256: {sha256_esquerda}
- Direita: {fonte_direita} — SHA-256: {sha256_direita}
- Data de geracao: {data_geracao}

## Divergencias

[Lista das ate 20 principais divergencias — PII mascarado]

- Chave {chave}:
  - {coluna}: {valor_left} != {valor_right} ({motivo: so_esquerda|so_direita|valor_diferente|status_divergente})

## Notas de Auditabilidade

- Divergencias com motivo classificado; nenhuma omitida.
- PII mascarado em todos os valores de exemplo.
- Reexecute com os mesmos parametros e fontes (via sha256) para reproduzir.

---
*Separacao: Fatos (valores diretos das fontes) x Inferencias (classificacao de motivo pelo agente)*
