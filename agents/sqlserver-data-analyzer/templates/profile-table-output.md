# SQL Server Table Profile

## Contrato de saída

Campos de contexto:
- **Schema:** `<schema>`
- **Table:** `<table>`
- **Row count:** `<inteiro>`

Tabela de perfil por coluna (máximo 30 colunas):

| column_name | null_count | distinct_count |
|-------------|-----------|----------------|
| id          | 0         | 1000           |
| name        | 12        | 998            |

Interpretação automática:
- `null_count == row_count` → coluna inutilizável.
- `distinct_count == 1` → coluna constante.
- `distinct_count == row_count` → candidato a chave única.
- `null_count / row_count > 0.5` → alta taxa de nulos.

Formato JSON (para encadeamento):
```json
{
  "schema": "dbo",
  "table": "customers",
  "row_count": 1000,
  "columns": [
    {"column_name": "id", "null_count": 0, "distinct_count": 1000}
  ]
}
```
