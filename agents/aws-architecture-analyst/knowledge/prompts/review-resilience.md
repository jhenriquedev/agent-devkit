# Prompt: Review Resilience

## Objetivo
Identificar sinais de fragilidade de resiliencia a partir do inventario,
separando achados confirmados, riscos potenciais e lacunas de dados.

## Entradas esperadas
- inventory.json (obrigatorio).

## Passos de raciocinio
1. Para cada recurso relevante, avalie sinais: Multi-AZ, DLQ em filas, VPC em
   Lambda, autoscaling, backups, single points of failure.
2. Quando um atributo necessario nao foi coletado (ex.: has_dlq ausente),
   registre como LACUNA DE DADOS, nao como "ok".
3. Aplique a rubrica de severidade de knowledge/rubrics.md.

## Regras de decisao (rubrica)
- high: recurso critico sem redundancia/backup confirmados.
- medium: fila sem DLQ confirmada; ponto unico provavel.
- info: configuracao a validar (ex.: Lambda sem VPC pode ser esperado).
- gap: atributo ausente => finding de severidade info com tipo "gap" pedindo
  coleta adicional.

## Formato de saida
- resilience-review.md (Achados confirmados / Riscos potenciais / Lacunas),
  resilience-findings.json (severity, message, confidence).

## Nao faca
- Nao reporte "nenhum risco" se o inventario nao tinha os atributos necessarios.
