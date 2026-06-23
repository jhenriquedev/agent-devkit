# Networking Review

> Contrato de saida: capability `review-networking`
> Cada finding: severity (high|medium|gap), message, confidence.

## Achados Confirmados
Riscos de rede suportados por atributos coletados:
| Severidade | Recurso | Mensagem | Confianca |
|---|---|---|---|

## Riscos Potenciais
Sinais de exposicao com confianca `inferred`:
| Severidade | Recurso | Mensagem | Confianca |
|---|---|---|---|

## Lacunas de Dados (gap)
| Campo Ausente | Recurso | Coleta Necessaria |
|---|---|---|
| `public_ip` | instancias EC2 | ampliar collector ec2.describe-instances |
| VPC/subnets/SGs | (nao coletados) | executar ec2.describe-vpcs / describe-security-groups |

> AVISO: sem os campos de rede coletados, NAO e possivel afirmar "sem exposicao
> publica". A ausencia de findings de networking pode refletir ausencia de dados.

---
*FATOS: findings baseados em campos de rede presentes no inventario.*
*LACUNAS: campos de rede nao coletados pelo discover atual.*

