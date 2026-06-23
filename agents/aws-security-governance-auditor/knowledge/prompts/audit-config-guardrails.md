# Capability: Auditar AWS Config Guardrails (read-only)

## Objetivo
Confirmar recorders e rules do AWS Config como guardrails de governança.

## Regras de decisão (rubrica)
- Nenhum configuration recorder → high, category=governance, status=confirmed.
- Recorder presente mas sem rules gerenciadas exigidas → medium.
- Rules não coletadas → LACUNA.

## Saída
findings[] resource_type=account. Recomendar habilitar recorders + managed rules.

## NÃO faça
Não crie recorders; apenas reporte e recomende.
