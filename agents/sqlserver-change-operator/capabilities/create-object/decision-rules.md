# Decision Rules: Create Object

- Criacao real de objeto exige `--execute`; sem a flag, retornar plano dry-run.
- Permitir apenas objetos de banco dentro do escopo aprovado, nunca objetos de servidor/login.
- Validar identificadores de schema, tabela, coluna, indice, view ou procedure antes de montar SQL.
- Bloquear comandos proibidos como `CREATE LOGIN`, `ALTER SERVER`, `GRANT`, `REVOKE` e `sp_configure`.
- Incluir script idempotente ou pre-check de existencia quando possivel.
- Usar `XACT_ABORT ON`, `LOCK_TIMEOUT` e timeout de statement.
- Registrar criacao no historico de mudancas quando executada.
- Para objetos que alteram contrato de dados, exigir plano de rollback ou remocao segura.
- Nunca imprimir connection string, senha, host completo ou URL completa.
- Nao criar objeto em schema inesperado sem confirmacao explicita.
