# Decision Rules: Run Write Script

- Executar script de escrita somente com `--execute`; sem a flag, retornar plano.
- Validar script contra keywords proibidas e multiplas operacoes perigosas antes da execucao.
- Exigir `WHERE` para `UPDATE` e `DELETE`; delete tambem exige `--confirm-delete`.
- Bloquear comandos de servidor, login, permissao, backup/restore, truncate e linked servers.
- Usar `XACT_ABORT ON`, `LOCK_TIMEOUT` e timeout de statement/conexao.
- Preferir transacao quando o script for transacional; documentar excecoes.
- Respeitar `max_affected_rows` e abortar quando exceder.
- Registrar alteracao e linhas afetadas no historico.
- Nunca imprimir connection string, senha, host completo ou URL completa.
- Em dry-run, mostrar risco, comandos normalizados e requisitos de confirmacao.
