# Database Change Operator

Agente especialista para aplicar mudancas controladas em banco PostgreSQL.

## Escopo inicial

- testar permissoes de escrita;
- planejar migrations;
- aplicar migrations;
- executar rollback;
- executar scripts de escrita controlados;
- realizar upsert por JSON;
- atualizar registros com preview de impacto;
- listar historico de migrations.

## Como usar

```bash
agent run database-change-operator test-write-permissions
agent run database-change-operator plan-migration --path migrations/202606211200_create_table.up.sql
agent run database-change-operator apply-migration --path migrations/202606211200_create_table.up.sql --execute
agent run database-change-operator migration-report
agent run database-change-operator plan-migration --database outro_banco --path migrations/202606211200_create_table.up.sql
```

Sem `--execute`, operacoes de escrita rodam como dry-run.
Quando `--database` for informado, o agente troca apenas o database da
connection string base. O banco alvo aparece como `Target database` na saida.

## Configuracao

```env
POSTGRES_DB_CONN_STRING=
POSTGRES_STATEMENT_TIMEOUT=15000
POSTGRES_LOCK_TIMEOUT=5000
```
