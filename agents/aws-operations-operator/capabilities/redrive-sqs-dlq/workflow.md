# Workflow: Redrive SQS DLQ

## Passos
1. Verificar que `--source-arn`, `--destination-arn` e `--environment` foram
   fornecidos. Se faltar, parar e perguntar.
2. O runner FORCA execute=False internamente — esta capability nunca executa,
   independente de qualquer flag passado pelo usuario.
3. Gerar plano e marcar status `blocked-plan-only` (destructive: true).
4. Explicar risco: redrive pode DUPLICAR processamento; consumidor deve ser idempotente.
5. Entregar rollback-notes alertando sobre duplicacao e orientando verificacao manual.

## Regras de decisao
- Mesmo que o usuario peca `--execute`, a capability retorna plano-only.
- Recomendacao obrigatoria: verificar idempotencia antes de qualquer execucao manual.
- Esta restricao e permanente no MVP e impostas no codigo do runner.

## Criterio de parada
Esta capability so gera plano. Nunca prossegue para mutacao.
