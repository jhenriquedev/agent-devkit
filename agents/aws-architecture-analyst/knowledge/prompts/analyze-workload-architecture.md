# Prompt: Analyze Workload Architecture

## Objetivo
Recortar de um inventario os recursos de um workload (por nome/prefixo/tag) e
descrever sua arquitetura: entrypoints, compute, dados, mensageria, rede, IAM.

## Entradas esperadas
- inventory.json (obrigatorio), workload OU resource_prefix.

## Passos de raciocinio
1. Filtre os recursos pelo workload/prefixo (match em name/id).
2. Agrupe por camada: entrypoints (API GW/ALB/CloudFront), compute (Lambda/ECS/
   EC2), dados (RDS/DynamoDB/S3), mensageria (SQS/SNS/EventBridge), rede (VPC/
   subnets/SGs), IAM (roles).
3. Avalie se o filtro provavelmente captura TODO o workload ou so parte.
4. Liste perguntas abertas (criticidade, owners, limites do workload).

## Regras de decisao
- Filtro por substring e heuristico: sempre questione se ha recursos do workload
  com nomenclatura diferente que ficaram de fora.
- Recurso sem tags de ownership/ambiente => perguntar, nao assumir.

## Formato de saida
- workload-architecture.md (por camada), workload-components.json,
  workload-open-questions.md.

## Nao faca
- Nao afirme que o recorte e completo. Nao infira criticidade sem evidencia.
