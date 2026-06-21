# Workflow

Consultar CPF na base restritiva via `sqlserver-data-analyzer`. A consulta deve
ser read-only e a saida deve mascarar CPF.

## Entradas

- `--cpf`: CPF a consultar. Pode vir formatado ou apenas com digitos.
- `--database`: database alternativo acessivel pela connection string.
- `--schema`, `--table`, `--cpf-column`: quando informados juntos, a capability
  consulta uma fonte explicita.
- `--limit`: limite por tabela candidata.
- `--format json`: contrato estruturado para outro agente consumir.

## Fonte de credencial

A capability prioriza `DB_RESTRICTIVE_CONN_STRING` do `.env` local. Se ela nao
existir, usa `SQLSERVER_DB_CONN_STRING`. O segredo nao deve aparecer na saida.

## Comportamento

1. Normalizar CPF para 11 digitos.
2. Se `schema/table/cpf-column` forem informados, consultar apenas essa origem.
3. Caso contrario, descobrir colunas de CPF via
   `sqlserver-data-analyzer/search-columns`.
4. Consultar candidatos via `sqlserver-data-analyzer/run-readonly-query`.
5. Retornar `hit`, `clear`, `skipped` ou `unavailable`.
6. Mascarar CPF e manter erros por origem sem abortar o runbook N1.
