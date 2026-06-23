# Observability Review

> Contrato de saida: capability `review-observability`
> Cada finding: severity (medium|info|gap), message, confidence.

## Achados Confirmados
Riscos de observabilidade suportados por atributos coletados:
| Severidade | Recurso | Mensagem | Confianca |
|---|---|---|---|

## Riscos Potenciais
Sinais com confianca `inferred`:
| Severidade | Recurso | Mensagem | Confianca |
|---|---|---|---|

## Lacunas de Dados (gap)
| Campo Ausente | Servico | Coleta Necessaria |
|---|---|---|

> NOTA: "nenhum alarm no inventario" pode significar que alarms existem mas nao
> foram coletados. Verifique as lacunas de coleta em collection-metadata.json.

---
*FATOS: findings baseados em recursos CloudWatch presentes no inventario.*
*LACUNAS: servicos cujo collector nao foi executado ou falhou.*

