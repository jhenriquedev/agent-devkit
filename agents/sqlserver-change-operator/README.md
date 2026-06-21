# SQL Server Change Operator

Agente especialista para mudancas controladas em Microsoft SQL Server.

## Escopo inicial

- testar permissoes de escrita com rollback;
- planejar migrations;
- aplicar migrations com historico e checksum;
- executar rollback;
- rodar scripts T-SQL controlados;
- criar objetos por SQL revisado;
- atualizar registros com `WHERE` obrigatorio;
- remover registros com confirmacao e limite;
- fazer upsert de JSON/CSV;
- criar backup logico de registros;
- consultar historico de mudancas.

## Como usar

```bash
./ai-devkit run sqlserver-change-operator plan-migration --path migrations/001_create_table.up.sql
./ai-devkit run sqlserver-change-operator apply-migration --path migrations/001_create_table.up.sql --rollback-path migrations/001_create_table.down.sql --execute
./ai-devkit run sqlserver-change-operator update-records --schema dbo --table Customers --set-json '{"status":"inactive"}' --where "id = 1"
./ai-devkit run sqlserver-change-operator delete-records --schema dbo --table Customers --where "id = 1" --confirm-delete --execute
```

## Configuracao

Use `.env` local:

```env
SQLSERVER_DB_CONN_STRING=
SQLSERVER_STATEMENT_TIMEOUT=15000
SQLSERVER_LOCK_TIMEOUT=5000
SQLSERVER_MAX_AFFECTED_ROWS=100
SQLSERVER_CHANGE_SCHEMA=ai_devkit
```

Todas as escritas reais exigem `--execute`.
