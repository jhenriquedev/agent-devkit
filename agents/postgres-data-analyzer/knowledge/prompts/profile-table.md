# Prompt: profile-table

> Operação read-only. Não exiba valores individuais de colunas PII. Separe dados de inferências.

## Objetivo
Gerar perfil agregado de uma tabela (por coluna: total_rows, null_count, distinct_count)
sem expor valores individuais, para entender qualidade e distribuição dos dados.

## Entradas esperadas
- `schema` (obrigatório).
- `table` (obrigatório).
- `limit_columns` (default 30): máximo de colunas a perfilar.
- `database` (opcional).

## Passos de raciocínio
1. Execute `profile-table`.
2. Para cada coluna calcule:
   - `null_ratio = null_count / total_rows`
   - `distinct_ratio = distinct_count / total_rows`
3. Sinalize (INFERÊNCIA):
   - `distinct_count == total_rows` → candidata a chave primária.
   - `distinct_count == 1` com `total_rows > 1` → coluna constante (sem poder discriminativo).
   - `null_ratio > 0.5` → alto null (ver `data_quality_thresholds` em policies.yaml).

## Regras de decisão
- `null_ratio > 0.5` = "alto null" → sinalizar com aviso.
- Coluna constante (`distinct == 1`) → sinalizar como possível candidata a remoção — INFERÊNCIA.
- Não liste valores distintos individuais se a coluna parecer PII por nome.

## Saída
Tabela: `column_name`, `data_type`, `total_rows`, `null_count`, `null_ratio`, `distinct_count`.
Seção **Sinais (INFERÊNCIA)**: candidatas a chave, colunas constantes, alto null.

## NÃO faça
- Não liste valores individuais de colunas PII.
- Não afirme que uma coluna "é" chave primária sem constraint confirmada.
