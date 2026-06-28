# Decision Rules: Update Records

- Update real exige `--execute`; sem a flag, retornar plano dry-run.
- Exigir `WHERE` explicito e rejeitar clausulas amplas como vazio, `1=1` ou `true`.
- Validar schema, tabela e colunas antes de montar SQL.
- Bloquear update em colunas sensiveis sem justificativa e escopo claros.
- Respeitar `max_affected_rows`; abortar quando estimativa ou resultado exceder limite.
- Usar transacao, `XACT_ABORT ON`, `LOCK_TIMEOUT` e timeout.
- Criar ou exigir backup logico quando rollback de dados for necessario.
- Registrar linhas afetadas, filtro, colunas alteradas e auditoria no schema configurado.
- Mascarar valores sensiveis em preview e relatorio.
- Nunca imprimir connection string, senha, host completo ou URL completa.
