# Decision Rules: Force ECS Deployment

## Objetivo de decisao

Forcar novo deployment de um ECS service com dry-run por padrao e execucao real
somente sob confirmacao forte.

## Entradas minimas

- `--cluster`, `--service` e `--environment` sao obrigatorios.
- `resource_id` deve ser exatamente `<cluster>/<service>`.
- Para executar, exigir `--execute` e
  `--confirm-resource <cluster>/<service>`.
- Em execucao real, a conta precisa estar na allowlist do ambiente.

## Quando executar

Execute em dry-run quando:

- o usuario quer reciclar tasks via novo deployment;
- ha cluster, service e ambiente explicitos;
- o operador quer ver comando, impacto e rollback antes de agir.

Execute de fato apenas quando:

- o dry-run foi revisado;
- `confirm-resource` bate exatamente com o `resource_id`;
- a conta AWS foi validada por `sts get-caller-identity`;
- preflight passou.

Nao execute quando:

- o usuario usar `prod` ou `production`; exigir `prd`;
- `confirm-resource` estiver ausente ou divergente;
- a conta nao estiver allowlisted para o ambiente;
- o service ou cluster estiver ambiguo.

## Regras de decisao

1. Sem `--execute`, persistir somente plano e dry-run.
2. Em `prd`, destacar reciclagem de tasks, possivel capacidade reduzida e
   impacto parcial durante rollout.
3. Preflight deve consultar estado do ECS service antes da mutacao.
4. Post-check deve consultar o service apos a mutacao.
5. Returncode diferente de zero deve falhar explicitamente.
6. Nao tratar force deployment como rollback; rollback exige nova acao com task
   definition validada.

## Criterios de qualidade

- Dry-run gera `operation-plan.md`, `operation-dry-run.json` e
  `rollback-notes.md`.
- Execucao real gera tambem `account-validation.json`, `preflight.json`,
  `post-check.json` e `operation-result.json`.
- Artefatos mostram comando e recurso confirmado sem expor credenciais.

## Escalacao

Pedir revisao humana antes de execucao em `prd`, quando o service for critico ou
quando running count/preflight indicar capacidade insuficiente.
