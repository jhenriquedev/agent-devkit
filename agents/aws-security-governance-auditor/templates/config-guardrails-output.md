# AWS Config Guardrails Audit — Contrato de Saída

> Fatos (fonte): `configservice describe-configuration-recorders` + `configservice describe-config-rules` na região configurada.
> Inferências (agente): severidade determinística por `audit_config_guardrails` (auditors.py).

## Formato real emitido por `render_findings` (report_renderer.py)

```
# Config Guardrails Audit

- [high] No AWS Config configuration recorders found - `account/<account_id>`
  - Evidencia: describe-configuration-recorders returned empty list.
  - Recomendacao: Enable AWS Config with at least one configuration recorder in the region.
```

## Artefatos gerados

- `config-guardrails-audit.json` — `{ account_id, region, audit: "config", finding_count: N, findings: [...] }`
- `config-guardrails-audit.md` — relatório humano

## LACUNA DE COLETA

Se nenhuma região for especificada, `config` não é coletado e o gap é registrado
em `snapshot.gaps`. Ausência de recorders é achado high confirmado, não LACUNA.
