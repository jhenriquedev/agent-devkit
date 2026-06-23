# Workflow: Plan Operational Action

## Passos
1. Verificar que `--operation` esta na allowlist (force-ecs-deployment,
   restart-ecs-service, invoke-lambda, invalidate-cloudfront-cache,
   scale-autoscaling-group, toggle-eventbridge-rule, redrive-sqs-dlq,
   purge-sqs-queue-plan). Se nao, retornar erro imediatamente.
2. Verificar que `--resource-id` e `--environment` foram fornecidos.
   Se faltar qualquer um, parar e pedir ao usuario — nao adivinhar.
3. Executar o runner (sem `--execute`). O runner NUNCA chama AWS nesta capability.
4. Ler os artefatos gerados: operation-plan.md e operation-dry-run.json.
5. Se `destructive: true` no dry-run, sinalizar `blocked-plan-only` e explicar
   que execucao real esta bloqueada no MVP.

## Regras de decisao
- Operacao fora da allowlist => erro, nao plano.
- Falta resource_id ou environment => parar, perguntar.
- Esta capability nunca chama `--execute`; qualquer execucao real deve ser feita
  via a capability especifica da operacao.

## Criterio de parada
Parar antes de qualquer mutacao AWS. Esta capability e exclusivamente de planejamento.
