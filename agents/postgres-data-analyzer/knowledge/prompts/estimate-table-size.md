# Prompt: estimate-table-size

> Operação read-only. Estimativas do planner — não são contagens exatas. Separe dados de inferências.

## Objetivo
Estimar o tamanho de tabelas (em bytes e número de linhas) usando estatísticas do
pg_class para priorizar análises e identificar tabelas grandes.

## Entradas esperadas
- `schema` (opcional): restringir ao schema.
- `limit` (default 50): número de tabelas a retornar.
- `database` (opcional).

## Passos de raciocínio
1. Execute `estimate-table-size`.
2. Leia resultados ordenados por tamanho (bytes) decrescente.
3. Apresente tabela com `table_schema`, `table_name`, `estimated_rows`, `total_bytes`.
4. **Marque como INFERÊNCIA**: `estimated_rows` vem de `pg_class.reltuples` — pode estar
   desatualizado se `ANALYZE` não foi executado recentemente.

## Regras de decisão
- Tabela com `estimated_rows > 1.000.000` → sinalizar como "grande"; recomendar uso de
  `profile-table` com `limit_columns` reduzido.
- `estimated_rows` desatualizado (sem ANALYZE recente) → INFERÊNCIA.

## Saída
Tabela: `table_schema`, `table_name`, `estimated_rows`, `total_bytes`.
Ordenada por `total_bytes` DESC.
Nota: "⚠ INFERÊNCIA: estimated_rows usa estatísticas do planner (reltuples); pode estar desatualizado."

## NÃO faça
- Não trate `estimated_rows` como contagem exata.
- Não leia dados de linha.
