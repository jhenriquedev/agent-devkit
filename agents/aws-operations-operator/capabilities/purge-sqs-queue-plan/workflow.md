# Workflow: Purge SQS Queue Plan

## Passos
1. Verificar que `--queue-url` e `--environment` foram fornecidos.
   Se faltar, parar e perguntar.
2. O runner FORCA execute=False internamente — nunca executa, independente de flags.
3. Gerar plano e marcar status `blocked-plan-only` (destructive: true).
4. Deixar EXPLICITO: purge apaga TODAS as mensagens da fila sem possibilidade de rollback.
5. Entregar rollback-notes orientando backup/reprocessamento antes de qualquer
   execucao manual fora do agente.

## Regras de decisao
- NUNCA executar, mesmo com `--execute`. Restricao imposta no codigo do runner.
- Mensagem de aviso de perda total e obrigatoria no plano.

## Criterio de parada
Esta capability so gera plano. Nunca prossegue para mutacao.
