# Contexto

- Este agente executa mudancas controladas em PostgreSQL.
- A connection string vem de `POSTGRES_DB_CONN_STRING` e define o banco padrao.
- O input opcional `--database` troca apenas o database da URL base, mantendo host, porta, usuario, senha e SSL.
- Escritas reais sempre exigem `--execute`.
- Migrations devem ser planejadas antes de aplicadas.
- Migrations destrutivas precisam de rollback.
- Historico e registrado em `ai_devkit_migrations`.
