# Prompt: Force ECS Deployment

## Objetivo
Forcar um novo deployment de um ECS service (`ecs update-service
--force-new-deployment`), reciclando as tasks com a task definition atual.

## Entradas esperadas
- cluster, service, environment (req). Opcionais: region, profile, execute,
  confirm_resource (= "<cluster>/<service>"), output_dir.

## Passos de raciocinio
1. Montar resource_id = "<cluster>/<service>".
2. Sempre comecar em dry-run; mostrar o comando exato.
3. Para executar: exigir `--execute` + `--confirm-resource <cluster>/<service>` +
   `--environment` explicito. Em prd, alertar sobre reciclagem de tasks/downtime
   parcial durante o rollout.
4. Na execucao, o repository valida conta, roda preflight (describe-services) e
   post-check (describe-services). Comparar status ACTIVE/running count antes/depois.

## Regras de decisao
- Sem confirm-resource => nao executar; explicar e mostrar o id a confirmar.
- environment `prod`/`production` => recusar; instruir `prd`.
- Conta fora da allowlist => abortar antes da mutacao.

## Formato de saida
Operacao, recurso, ambiente, conta validada, status do deployment, e diff
preflight->post-check (status/running count). Caminho dos artefatos.

## NAO fazer
- Nao alterar task definition. Nao executar sem confirmacao. Nao silenciar erros do
  AWS CLI (returncode != 0 => falha explicita).
