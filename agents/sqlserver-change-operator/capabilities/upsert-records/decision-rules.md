# Decision Rules: Upsert Records

- Upsert real exige `--execute`; sem a flag, retornar plano dry-run.
- Exigir chave natural ou coluna chave explicita presente em todos os registros.
- Validar schema, tabela, colunas e tipos antes de montar SQL.
- Preferir padrao seguro `IF EXISTS`/`UPDATE ELSE INSERT` ou equivalente controlado.
- Bloquear upsert sem limite de registros ou com payload ambiguo.
- Respeitar `max_affected_rows` somando inserts e updates.
- Usar transacao, `XACT_ABORT ON`, `LOCK_TIMEOUT` e timeout quando aplicavel.
- Registrar inserts, updates, chave usada e linhas afetadas na auditoria.
- Mascarar valores sensiveis em previews e relatorios.
- Nunca imprimir connection string, senha, host completo ou URL completa.
