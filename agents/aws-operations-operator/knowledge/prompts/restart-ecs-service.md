# Prompt: Restart ECS Service

## Objetivo
Reiniciar um ECS service de forma controlada via novo deployment forcado (mesma
mecanica de force-ecs-deployment, com identidade de operacao "restart-ecs-service").

## Entradas esperadas
cluster, service, environment (req); opcionais identicos a force-ecs-deployment.

## Passos de raciocinio
1. resource_id = "<cluster>/<service>".
2. Dry-run primeiro. Deixar claro que "restart" = rollout de novas tasks, nao stop/start.
3. Executar so com `--execute` + `--confirm-resource` + ambiente explicito.
4. Verificar estabilizacao: comparar tasks antigas/novas via preflight/post-check ate
   o service estabilizar (rollback_hint do repository orienta isso).

## Regras de decisao
- Mesmas guardas de execucao de force-ecs-deployment.
- Em prd, alertar que ha periodo de capacidade reduzida durante o rollout.

## Formato de saida
Operacao restart-ecs-service, recurso, ambiente, status do deployment, observacao de
estabilizacao. Caminho dos artefatos.

## NAO fazer
- Nao confundir com stop de tasks. Nao executar sem confirmacao.
