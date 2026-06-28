# Decision Rules: Rollback Migration

- Rollback real exige `--execute`; sem a flag, retornar plano dry-run.
- Executar rollback somente para migration registrada ou rollback explicitamente informado.
- Verificar ordem, dependencias e estado atual antes de reverter.
- Bloquear rollback que contenha comandos proibidos ou risco de servidor.
- Usar transacao, `XACT_ABORT ON`, `LOCK_TIMEOUT` e timeout quando o script permitir.
- Para rollback destrutivo, exigir confirmacao e backup quando aplicavel.
- Registrar rollback no historico com migration, motivo, operador e resultado.
- Respeitar limite de linhas afetadas quando o rollback tocar dados.
- Nunca imprimir connection string, senha, host completo ou URL completa.
- Se o estado estiver divergente, abortar e pedir analise manual em vez de tentar compensacao cega.
