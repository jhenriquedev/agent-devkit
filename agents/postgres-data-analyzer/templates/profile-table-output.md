# Postgres Table Profile

- Database: <database>
- Schema: <schema>
- Table: <table>
- Row count: <row_count>

| column_name | data_type | total_rows | null_count | null_ratio | distinct_count |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |

## Sinais (INFERÊNCIA)

- Candidatas a chave (distinct_count == total_rows): ...
- Colunas constantes (distinct_count == 1): ...
- Alto null (null_ratio > 0.5): ...

<!-- Dados coletados: profile_table(schema, table). Sinais são inferência, não fatos. -->
