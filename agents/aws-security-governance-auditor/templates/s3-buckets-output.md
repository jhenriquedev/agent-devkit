# S3 Buckets Audit — Contrato de Saída

> Fatos (fonte): buckets via `s3api list-buckets`; PAB via `s3api get-public-access-block`; encryption via `s3api get-bucket-encryption`.
> Inferências (agente): severidade determinística por `audit_s3_buckets` (auditors.py).

## Formato real emitido por `render_findings` (report_renderer.py)

```
# S3 Buckets Audit

- [high] S3 bucket missing Public Access Block - `<bucket-name>`
  - Evidencia: BlockPublicAcls=false (or flag absent).
  - Recomendacao: Enable all four Public Access Block flags on the bucket.

- [medium] S3 bucket missing server-side encryption - `<bucket-name>`
  - Evidencia: No ServerSideEncryptionConfiguration found.
  - Recomendacao: Enable SSE-S3 or SSE-KMS default encryption.
```

## Artefatos gerados

- `s3-buckets-audit.json` — `{ account_id, region, audit: "s3", finding_count: N, findings: [...] }`
- `s3-buckets-audit.md` — relatório humano

## LACUNA DE COLETA

Se PAB ou Encryption de um bucket não puderem ser coletados, um gap é registrado em
`snapshot.gaps` e o bucket é reportado como LACUNA (não como "seguro").
