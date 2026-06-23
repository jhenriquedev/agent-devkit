# Postgres Data Report — <schema>.<table>

## Escopo

- Database: <database> | Schema: <schema> | Tabela: <table> | Total de linhas: <row_count>

## Dados coletados

### Colunas Sensíveis

> ⚠ INFERÊNCIA: classificação por heurística de nome de coluna.

| column_name | sensitive_kind |
|---|---|
| ... | ... |

### Colunas com Alto Null (null_ratio > 0.5)

| column_name | null_ratio |
|---|---|
| ... | ... |

### Perfil de Colunas

| column_name | data_type | total_rows | null_count | distinct_count |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## Inferências e Recomendações

- Revisar colunas sensíveis antes de compartilhar resultados.
- Investigar colunas com alto null antes de usar em análises.

<!-- Dados coletados: profile_table + detect_sensitive_columns. Recomendações = inferência. -->
