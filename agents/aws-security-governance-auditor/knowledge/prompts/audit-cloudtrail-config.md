# Capability: Auditar CloudTrail (read-only)

## Objetivo
Verificar existência e integridade de trilhas CloudTrail.

## Regras de decisão (rubrica)
- Nenhum trail presente → critical, category=cloudtrail, status=confirmed.
- Trail presente mas sem log file validation / multi-region / storage central →
  high (quando o status for coletado).
- Status do trail não coletado → LACUNA.

## Saída
findings[] resource_type=account/trail. Recomendar trail org/account com validação
e storage centralizado.

## NÃO faça
Não habilite trilhas; apenas reporte e recomende.
