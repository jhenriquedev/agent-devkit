# AWS Operations Operator

Agente especialista em operacoes AWS controladas. Todas as capabilities operam
em dry-run por padrao.

## Exemplos

Configure as contas permitidas antes de qualquer execucao real:

```bash
export AWS_OPERATIONS_ALLOWED_ACCOUNTS_DEV=111111111111
export AWS_OPERATIONS_ALLOWED_ACCOUNTS_PRD=333333333333
export AWS_OPERATIONS_DEFAULT_REGION_DEV=us-east-1
export AWS_OPERATIONS_DEFAULT_REGION_PRD=us-east-1
```

```bash
agent run aws-operations-operator force-ecs-deployment \
  --cluster orders \
  --service orders-api \
  --environment dev \
  --output-dir ops/orders \
  --yes-create-dir

agent run aws-operations-operator force-ecs-deployment \
  --cluster orders \
  --service orders-api \
  --environment prd \
  --execute \
  --confirm-resource orders/orders-api \
  --output-dir ops/orders-prd \
  --yes-create-dir
```

## Guardrails

- Sem `--execute`, nenhuma chamada mutavel e executada.
- Sem `--confirm-resource`, `--execute` falha.
- Execucao real chama `sts get-caller-identity` e valida a conta contra
  `AWS_OPERATIONS_ALLOWED_ACCOUNTS_<ENV>`.
- Execucao real gera `account-validation.json`, `preflight.json`,
  `post-check.json` e `operation-result.json`.
- Payload de Lambda e redigido nos artefatos; o agente registra hash e tamanho,
  nao o conteudo bruto.
- Operacoes destrutivas geram plano, mas nao executam no MVP.
