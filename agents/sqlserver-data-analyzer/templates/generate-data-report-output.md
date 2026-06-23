# SQL Server Data Report

## Contrato de saída

Relatório em seções com separação explícita de **coletado** × **inferido**:

### Summary
- Schema: `<schema>`
- Table: `<table>` (se fornecida)

### Profile (coletado — apenas se schema+table)
Tabela de stats por coluna. Ver `profile-table-output.md`.

### Quality Issues (coletado — apenas se schema+table)
Lista de issues por coluna (`all_null`, `constant_value`).

### Sensitive Columns (INFERÊNCIA por padrão de nome)
Tabela `table_schema | table_name | column_name | sensitive_kind`.
Nota obrigatória: "Classificação por padrão de nome — pode ter falso
positivo/negativo. Confirme por amostra mascarada."

### Relationships (coletado — FKs declaradas)
Tabela de FKs. Ver `list-relationships-output.md`.

---
Dados pessoais brutos nunca são incluídos no relatório.

Formato JSON (para encadeamento):
```json
{
  "profile": {"row_count": 1000, "columns": []},
  "quality_issues": {"issues": []},
  "sensitive_columns": {"columns": []},
  "relationships": {"relationships": []}
}
```
