# Decision Rules: Delete Records

- Delete real exige `--execute` e `--confirm-delete`.
- Exigir `WHERE` explicito e rejeitar clausulas amplas como vazio, `1=1` ou `true`.
- Bloquear `TRUNCATE`, `DROP`, comandos de servidor e qualquer delete sem escopo.
- Exigir backup logico previo quando houver necessidade de rollback de dados.
- Respeitar `max_affected_rows`; abortar se a contagem estimada ou real exceder o limite.
- Usar transacao, `XACT_ABORT ON`, `LOCK_TIMEOUT` e timeout quando o delete permitir.
- Registrar linhas afetadas e detalhes de auditoria no schema configurado.
- Mascarar valores sensiveis em previews e relatorios.
- Nunca imprimir connection string, senha, host completo ou URL completa.
- Em dry-run, mostrar tabela, filtro, risco e comando planejado sem executar.
