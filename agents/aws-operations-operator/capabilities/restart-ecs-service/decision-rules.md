# Decision Rules: Restart ECS Service

## Objetivo de decisao

Planejar ou executar restart controlado de ECS service por meio de novo
deployment, sem stop/start direto de tasks.

## Entradas minimas

- `--cluster`, `--service` e `--environment` sao obrigatorios.
- `resource_id` deve ser `<cluster>/<service>`.
- Execucao real exige `--execute`, `--confirm-resource` identico ao
  `resource_id` e conta allowlisted.

## Quando executar

Execute em dry-run quando:

- o objetivo e reciclar tasks de forma controlada;
- o operador precisa revisar comando e impacto;
- o ambiente foi informado.

Execute de fato apenas quando:

- o plano foi revisado;
- o operador confirmou o recurso exato;
- preflight e validacao de conta passaram.

Nao execute quando:

- o pedido for para matar tasks individualmente;
- `confirm-resource` estiver ausente ou errado;
- a conta nao estiver autorizada para o ambiente;
- `environment` usar alias de producao diferente de `prd`.

## Regras de decisao

1. Restart significa novo deployment ECS, nao parada direta de containers.
2. Em `prd`, destacar risco de downtime parcial e capacidade reduzida.
3. Comparar preflight e post-check para service status e running task count.
4. Nao mascarar falha de AWS CLI; returncode diferente de zero bloqueia sucesso.
5. Rollback e operacional: validar task definition anterior e executar novo
   deployment se necessario.

## Criterios de qualidade

- Dry-run contem comando `ecs update-service --force-new-deployment`.
- Execucao real gera validacao de conta, preflight, post-check e resultado.
- O relatorio deixa claro que a acao nao garante rollback automatico.

## Escalacao

Pedir confirmacao adicional quando o service for de producao, tiver baixa
redundancia ou o preflight indicar desired/running count insuficiente.
