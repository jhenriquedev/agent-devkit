# Security Groups Audit — Contrato de Saída

> Fatos (fonte): `ec2 describe-security-groups` na região configurada.
> Inferências (agente): severidade determinística por `audit_security_groups` (auditors.py).

## Formato real emitido por `render_findings` (report_renderer.py)

```
# Security Groups Audit

- [critical] Security group allows unrestricted SSH/RDP access - `<sg-id>`
  - Evidencia: Ingress rule 0.0.0.0/0 on port 22 (or 3389).
  - Recomendacao: Restrict SSH/RDP to specific trusted CIDR ranges.

- [high] Security group allows unrestricted access on port <N> - `<sg-id>`
  - Evidencia: Ingress rule 0.0.0.0/0 on port <N>.
  - Recomendacao: Restrict to required CIDR ranges only.
```

## Artefatos gerados

- `security-groups-audit.json` — `{ account_id, region, audit: "security_groups", finding_count: N, findings: [...] }`
- `security-groups-audit.md` — relatório humano

## LACUNA DE COLETA

Se nenhuma região for especificada, `security_groups` não é coletado e o gap é
registrado em `snapshot.gaps`.
