# Secrets Usage Audit — Contrato de Saída

> Fatos (fonte): `secretsmanager list-secrets` na região configurada (inclui campo `RotationEnabled`).
> Inferências (agente): severidade determinística por `audit_secrets_usage` (auditors.py).

## Formato real emitido por `render_findings` (report_renderer.py)

```
# Secrets Usage Audit

- [medium] Secret rotation not enabled - `<secret-name>`
  - Evidencia: RotationEnabled=false (or field absent).
  - Recomendacao: Enable automatic rotation for this secret using AWS Secrets Manager rotation.
```

## Artefatos gerados

- `secrets-usage-audit.json` — `{ account_id, region, audit: "secrets", finding_count: N, findings: [...] }`
- `secrets-usage-audit.md` — relatório humano

## LACUNA DE COLETA

Se nenhuma região for especificada, `secrets` não é coletado e o gap é registrado
em `snapshot.gaps`. Ausência de `RotationEnabled` é tratada como `false` (não como "rotação ativa").
