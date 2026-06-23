# Resilience Review

> Contrato de saida: capability `review-resilience`
> Cada finding: severity (high|medium|info|gap), message, confidence.

## Achados Confirmados
Riscos de resiliencia suportados por atributos coletados:
| Severidade | Recurso | Mensagem | Confianca |
|---|---|---|---|

## Riscos Potenciais
Sinais de fragilidade com confianca `inferred`:
| Severidade | Recurso | Mensagem | Confianca |
|---|---|---|---|

## Lacunas de Dados (gap)
Atributos necessarios para a avaliacao que nao foram coletados:
| Campo Ausente | Recurso | Coleta Necessaria |
|---|---|---|
| `has_dlq` | `{fila_sqs}` | `sqs.get-queue-attributes` |
| `public_ip` | `{instancia_ec2}` | ampliar collector ec2 |

> NOTA: findings do tipo `gap` NAO significam "sem risco". Significam que os
> dados para avaliar o risco estao ausentes. Ver knowledge/rubrics.md.

---
*FATOS: findings baseados em atributos presentes no inventario.*
*INFERENCIAS: findings baseados em ausencia de atributo esperado.*
*LACUNAS: atributos necessarios nao coletados pela descoberta atual.*

