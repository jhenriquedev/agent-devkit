# AWS Operations Operator

Agente especialista em operacoes AWS controladas. Todas as capabilities operam
em dry-run por padrao.

## Exemplos

```bash
./ai-devkit run aws-operations-operator force-ecs-deployment \
  --cluster orders \
  --service orders-api \
  --environment dev \
  --output-dir ops/orders \
  --yes-create-dir

./ai-devkit run aws-operations-operator force-ecs-deployment \
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
- Operacoes destrutivas geram plano, mas nao executam no MVP.
