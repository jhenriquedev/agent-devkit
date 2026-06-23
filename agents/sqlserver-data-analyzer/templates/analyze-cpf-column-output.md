# SQL Server CPF Analysis

## Contrato de saída

Métricas agregadas (nunca CPFs individuais):

| Métrica                     | Valor |
|-----------------------------|-------|
| total_rows                  | N     |
| blank_count                 | N     |
| invalid_format_count        | N     |
| repeated_digits_count       | N     |
| valid_count                 | N     |
| invalid_check_digit_count   | N     |
| duplicated_document_count   | N     |
| duplicated_row_count        | N     |

Interpretação por rubrica:
- blank_count/total_rows > 10% → preenchimento ruim.
- repeated_digits_count > 0 → placeholders inválidos.
- invalid_check_digit_count/total_rows > 5% → problema de captura.
- duplicated_document_count > 0 → investigar fraude/erro de integração.

CPFs individuais NUNCA são exibidos.

Formato JSON (para encadeamento):
```json
{
  "schema": "dbo",
  "table": "customers",
  "column": "cpf",
  "total_rows": 1000,
  "blank_count": 5,
  "valid_count": 980
}
```
