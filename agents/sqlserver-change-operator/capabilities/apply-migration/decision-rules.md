# Decision Rules: Apply Migration

- Aplicar migration real somente com `--execute`; sem a flag, retornar plano dry-run.
- Exigir plano previo da migration com risco, comandos, rollback e limite de impacto.
- Bloquear keywords proibidas por `knowledge/policies.yaml`, incluindo comandos de servidor e login.
- Usar `XACT_ABORT ON`, `LOCK_TIMEOUT` e statement timeout antes da execucao.
- Preferir transacao quando o SQL for transacional; documentar quando nao for.
- Migration destrutiva exige rollback disponivel e confirmacao explicita.
- Registrar migration aplicada em `ai_devkit.schema_migrations` ou schema configurado.
- Respeitar `max_affected_rows`; se exceder, abortar e exigir limite explicito.
- Nunca imprimir connection string, senha, host completo ou URL completa.
- Em falha, reportar estado, erro resumido e proximo passo sem expor segredo.
