# Workflow: Restart ECS Service

## Passos
1. Verificar que `--cluster`, `--service` e `--environment` foram fornecidos.
   Se faltar, parar e perguntar.
2. Montar resource_id = "<cluster>/<service>". Esclarecer que "restart" significa
   rollout de novas tasks (nao stop/start direto).
3. Executar em dry-run. Apresentar o comando e o resource_id a confirmar.
4. Para executar: exigir `--execute` + `--confirm-resource <cluster>/<service>` +
   ambiente explicito. Em prd, alertar sobre periodo de capacidade reduzida.
5. Comparar preflight/post-check: status do service e running task count antes/depois.

## Regras de decisao
- Mesmas guardas de force-ecs-deployment (confirm-resource, prd exato, allowlist).
- Em prd: destacar que ha risco de downtime parcial durante o rollout.

## Criterio de parada
Abortar se: falta input, conta nao valida, confirm-resource incorreto, returncode != 0.
