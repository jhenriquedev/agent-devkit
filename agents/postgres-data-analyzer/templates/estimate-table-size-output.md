# Postgres Table Size Estimate

- Database: <database>

| table_schema | table_name | estimated_rows | total_bytes |
|---|---|---|---|
| ... | ... | ... | ... |

> ⚠ INFERÊNCIA: estimated_rows usa pg_class.reltuples — pode estar desatualizado
> se ANALYZE não foi executado recentemente.

<!-- Inferência: estimate_table_size() — reltuples do planner. Ordenado por total_bytes DESC. -->
