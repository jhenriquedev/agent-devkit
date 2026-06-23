# Public Exposure Audit — Contrato de Saída

> Fatos (fonte): S3 PAB via `s3api get-public-access-block`; Security Groups via `ec2 describe-security-groups`.
> Inferências (agente): severidade determinística por `audit_public_exposure` (auditors.py).

## Formato real emitido por `render_findings` (report_renderer.py)

```
# Public Exposure Audit

- [critical] Security group allows unrestricted SSH access - `<sg-id>`
  - Evidencia: Ingress rule 0.0.0.0/0 on port 22.
  - Recomendacao: Restrict SSH to trusted CIDR ranges.

- [high] S3 bucket missing Public Access Block - `<bucket-name>`
  - Evidencia: RestrictPublicBuckets=false.
  - Recomendacao: Enable all four Public Access Block flags.
```

## Artefatos gerados

- `public-exposure-audit.json` — `{ account_id, region, audit: "public_exposure", finding_count: N, findings: [...] }`
- `public-exposure-audit.md` — relatório humano

## LACUNA DE COLETA

Se região não especificada, security groups não são coletados (gap registrado).
Se PAB de bucket falhar, gap por bucket é registrado em `snapshot.gaps`.
