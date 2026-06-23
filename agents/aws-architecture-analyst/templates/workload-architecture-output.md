# Workload Architecture

> Contrato de saida: capability `analyze-workload-architecture`

## Escopo do Workload
- **Filtro/workload:** `{workload_or_prefix}`
- **Recursos encontrados:** N

> AVISO: o filtro por substring e heuristico. Recursos do workload com
> nomenclatura diferente podem ter ficado de fora.

## Componentes por Camada

### Entrypoints (API GW / ALB / CloudFront)
| Nome | Tipo | ID |
|---|---|---|

### Compute (Lambda / ECS / EC2)
| Nome | Tipo | ID |
|---|---|---|

### Dados (RDS / DynamoDB / S3)
| Nome | Tipo | ID |
|---|---|---|

### Mensageria (SQS / SNS / EventBridge)
| Nome | Tipo | ID |
|---|---|---|

### Rede (VPC / Subnets / SGs)
| Nome | Tipo | ID |
|---|---|---|

### IAM (Roles)
| Nome | Tipo | ID |
|---|---|---|

## Perguntas Abertas
- Confirmar criticidade e owners do workload.
- Verificar se ha recursos com prefixo diferente que pertencem ao workload.
- ...

---
*FATOS: recursos retornados pelo inventario que passaram no filtro.*
*LACUNAS: recursos possivelmente pertencentes ao workload mas fora do filtro.*

