# Decision Rules: Scale Auto Scaling Group

## Objetivo de decisao

Planejar ou executar ajuste de desired capacity de Auto Scaling Group com
`--honor-cooldown`, dry-run por padrao e confirmacao forte para execucao.

## Entradas minimas

- `--auto-scaling-group`, `--desired-capacity` e `--environment` sao
  obrigatorios.
- `resource_id` deve ser o nome exato do ASG.
- Execucao real exige `--execute`, `--confirm-resource <asg-name>` e conta
  allowlisted.

## Quando executar

Execute em dry-run quando:

- o usuario quer revisar alteracao de capacidade;
- desired capacity foi informado numericamente;
- o impacto de escala foi entendido.

Execute de fato apenas quando:

- preflight descreveu o ASG atual;
- desired capacity esta dentro de min/max esperado;
- `confirm-resource` bate com o ASG;
- conta foi validada para o ambiente.

Nao execute quando:

- desired capacity for incerto ou fora do intervalo operacional;
- scale-to-zero em `hml` ou `prd` nao tiver confirmacao adicional;
- cooldown/impacto de capacidade nao foi considerado.

## Regras de decisao

1. Sempre usar `autoscaling set-desired-capacity --honor-cooldown`.
2. `desired_capacity = 0` e risco de indisponibilidade; em `hml`/`prd`, exigir
   destaque e confirmacao humana antes de execucao.
3. Comparar capacidade preflight e post-check.
4. Rollback sugerido e restaurar desired capacity anterior.
5. Nao executar se conta nao estiver allowlisted.

## Criterios de qualidade

- Dry-run registra desired capacity alvo e comando.
- Execucao real gera `preflight.json`, `post-check.json` e
  `operation-result.json`.
- `rollback-notes.md` orienta restaurar capacidade anterior.

## Escalacao

Pedir aprovacao operacional quando reduzir capacidade em ambiente compartilhado,
quando desired capacity for zero ou quando o ASG sustentar workload critico.
