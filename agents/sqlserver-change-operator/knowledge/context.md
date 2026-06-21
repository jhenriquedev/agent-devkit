# Contexto

- O agente executa mudancas controladas em SQL Server.
- A connection string fica em `SQLSERVER_DB_CONN_STRING`.
- O schema de controle padrao e `ai_devkit`, configuravel por
  `SQLSERVER_CHANGE_SCHEMA`.
- Toda escrita real exige `--execute`.
- Dry-run deve mostrar plano, risco, comandos e proximo passo.
- Saidas humanas nao devem exibir connection strings nem segredos.
