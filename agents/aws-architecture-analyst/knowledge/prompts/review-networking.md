# Prompt: Review Networking

## Objetivo
Revisar exposicao e topologia de rede: VPC, subnets, route tables, load
balancers, security groups e IPs publicos.

## Entradas esperadas
- inventory.json (obrigatorio).

## Passos de raciocinio
1. Identifique recursos com exposicao publica (EC2 com IP publico, LB
   internet-facing).
2. Avalie SGs permissivos e subnets publicas com recursos sensiveis.
3. Quando o atributo (ex.: public_ip) nao foi coletado, registre lacuna.

## Regras de decisao (rubrica)
- high: recurso sensivel com exposicao publica direta inesperada.
- medium: EC2 com IP publico; SG 0.0.0.0/0 em porta administrativa.
- gap: campo de exposicao nao coletado pela descoberta => pedir coleta.

## Formato de saida
- networking-review.md, networking-findings.json.

## Nao faca
- Nao afirme "sem exposicao publica" se o inventario nao traz os campos de rede.
