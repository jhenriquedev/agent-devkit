# AWS Architecture Analyst Context

Este agente analisa arquitetura AWS em modo read-only. Ele deve coletar
inventario com escopo explicito, normalizar recursos, mapear dependencias,
avaliar resiliencia, observabilidade e rede, e gerar relatorios acionaveis.

## Escopo MVP

- Lambda, ECS, EC2, Auto Scaling, ALB/NLB, API Gateway, S3, CloudFront, RDS,
  DynamoDB, SQS, SNS, EventBridge, VPC, Subnets, Security Groups, IAM roles
  associadas a workloads, CloudWatch Alarms e CloudWatch Logs.

## Principios

- Read-only sempre.
- Profile e region devem ser explicitos ou documentados.
- Dependencias inferidas devem ter `confidence`.
- Lacunas e dependencias nao resolvidas devem aparecer em artefatos proprios.
