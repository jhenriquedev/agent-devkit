# SQL Server Read-Only Query

## Contrato de saída

Campos obrigatórios:
- **Row count:** `<inteiro>` — número de linhas retornadas.
- **Limit:** `<inteiro>` — limite aplicado via TOP.

Tabela de linhas (mascarada):
| col1 | col2 | ... |
|------|------|-----|
| val  | val  | ... |

Colunas com `sensitive_kind` (cpf, cnpj, email, phone, name, address, token,
password) são mascaradas automaticamente pelo runner. Dados pessoais nunca
aparecem brutos.

Se `row_count == limit`: pode haver mais linhas; refine o WHERE.

Formato JSON (para encadeamento):
```json
{
  "row_count": 42,
  "limit": 100,
  "rows": [{"col1": "val", "col2": "val"}]
}
```
