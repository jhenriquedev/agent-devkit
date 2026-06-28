# Decision Rules

- Rollback deve ser explicito e apontar para arquivo `.down.sql`.
- Nunca executar rollback sem `--execute`.
- Rollback tambem passa por classificacao de risco.
- Se o rollback falhar, retornar erro sem esconder stderr do `psql`.
- Nao inventar rollback automaticamente.
- Atualizar `ai_devkit_migrations` para registrar status `rolled_back`.
- Aplicar `statement_timeout` e `lock_timeout` na execucao.
