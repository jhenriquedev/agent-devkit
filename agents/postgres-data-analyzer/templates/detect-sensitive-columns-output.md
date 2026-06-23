# Postgres Sensitive Columns

- Database: <database>
- Count: <count>

| table_schema | table_name | column_name | data_type | sensitive_kind |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

> ⚠ INFERÊNCIA: classificação baseada em heurística de nome de coluna, não por conteúdo.
> Pode haver falso positivo e falso negativo.

<!-- Inferência: detect_sensitive_columns() — sensitive_kind por nome. -->
