# CloudTrail Audit — Contrato de Saída

> Fatos (fonte): `cloudtrail describe-trails` na região configurada.
> Inferências (agente): severidade determinística por `audit_cloudtrail_config` (auditors.py).

## Formato real emitido por `render_findings` (report_renderer.py)

```
# CloudTrail Audit

- [critical] No CloudTrail trails configured - `account/<account_id>`
  - Evidencia: describe-trails returned empty trailList.
  - Recomendacao: Create a multi-region CloudTrail trail with log file validation enabled.
```

## Artefatos gerados

- `cloudtrail-audit.json` — `{ account_id, region, audit: "cloudtrail", finding_count: N, findings: [...] }`
- `cloudtrail-audit.md` — relatório humano

## LACUNA DE COLETA

Se nenhuma região for especificada, `cloudtrail` não é coletado e o gap é registrado
em `snapshot.gaps`. Trails ausentes são achado crítico confirmado, não LACUNA.
