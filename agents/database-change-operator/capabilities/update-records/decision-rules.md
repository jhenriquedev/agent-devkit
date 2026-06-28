# Decision Rules

- Nao aceitar `where true` ou `where 1=1`.
- Nao atualizar sem `--execute`.
- Sempre gerar preview de linhas afetadas antes da escrita real.
- Usar para alteracoes pontuais e auditaveis.
- Para alteracoes estruturais, preferir migration.
- Respeitar `max_affected_rows`; volumes acima do limite exigem confirmacao reforcada.
- Registrar execucoes reais em `ai_devkit_write_audit`.
