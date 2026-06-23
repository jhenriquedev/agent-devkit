# Prompt: Plan Operational Action

## Objetivo
Gerar um plano + dry-run de uma operacao AWS suportada, SEM executar nenhuma
mutacao. Usar quando o usuario quer entender o impacto antes de agir, ou para
operacoes destrutivas (que so podem ser planejadas).

## Entradas esperadas
- operation: um id da allowlist de planejamento (force-ecs-deployment,
  restart-ecs-service, invoke-lambda, invalidate-cloudfront-cache,
  scale-autoscaling-group, toggle-eventbridge-rule, redrive-sqs-dlq,
  purge-sqs-queue-plan).
- resource_id: identificador do recurso alvo (ex.: cluster/service).
- environment: dev | hml | prd (explicito).

## Passos de raciocinio
1. Validar que `operation` esta na allowlist de planejamento. Se nao, recusar e
   listar operacoes validas.
2. Confirmar resource_id e environment presentes; se faltar, perguntar.
3. Rodar a capability (dry-run) e ler operation-plan.md + operation-dry-run.json.
4. Se `destructive: true`, sinalizar status `blocked-plan-only` e explicar que
   execucao real esta bloqueada no MVP.

## Regras de decisao
- Nunca executa AWS (esta capability so planeja).
- Operacao fora da allowlist => erro, nao plano.

## Formato de saida
Resumo: operacao, recurso, ambiente, destrutiva?, status do plano, e caminho dos
artefatos. Aponte o comando AWS do plano.

## NAO fazer
- Nao inventar resource_id. Nao assumir ambiente. Nao chamar `--execute`.
