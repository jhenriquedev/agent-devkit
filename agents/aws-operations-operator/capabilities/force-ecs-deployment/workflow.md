# Workflow: Force ECS Deployment

## Passos
1. Verificar que `--cluster`, `--service` e `--environment` foram fornecidos.
   Se faltar qualquer um, parar e pedir ao usuario.
2. Montar resource_id = "<cluster>/<service>".
3. Executar em dry-run (sem `--execute`). Apresentar o comando AWS exato e o
   resource_id a ser confirmado.
4. Se o usuario quiser executar: exigir `--execute` + `--confirm-resource <cluster>/<service>`
   + `--environment` explicito. Em prd, apresentar o impacto (reciclagem de tasks,
   downtime parcial) antes de aceitar execucao.
5. Na execucao, o repository: (a) valida conta via sts get-caller-identity vs allowlist,
   (b) roda preflight (describe-services), (c) executa o comando, (d) roda post-check.
6. Verificar returncode: se != 0, falha explicita — nao silenciar.

## Regras de decisao
- environment `prod` ou `production` => recusar; instruir `--environment prd`.
- Sem `--confirm-resource` => nao executar; mostrar o id correto a confirmar.
- `confirm-resource` != resource_id => abortar.
- Conta fora da allowlist => abortar antes da mutacao.

## Criterio de parada
Abortar se: falta input, conta nao validada, confirm-resource incorreto, ou
returncode != 0.
