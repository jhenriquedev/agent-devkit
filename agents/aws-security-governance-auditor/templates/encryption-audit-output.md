# Encryption Audit — Contrato de Saída

> Fatos (fonte): S3 encryption via `s3api get-bucket-encryption`; KMS via `kms list-keys` + `kms describe-key`.
> Inferências (agente): severidade determinística por `audit_encryption` (auditors.py).

## Formato real emitido por `render_findings` (report_renderer.py)

```
# Encryption Audit

- [medium] S3 bucket missing server-side encryption - `<bucket-name>`
  - Evidencia: No ServerSideEncryptionConfiguration found.
  - Recomendacao: Enable SSE-S3 or SSE-KMS default encryption on the bucket.
```

## Artefatos gerados

- `encryption-audit.json` — `{ account_id, region, audit: "encryption", finding_count: N, findings: [...] }`
- `encryption-audit.md` — relatório humano

## LACUNA DE COLETA

Se `get-bucket-encryption` falhar por bucket (ex.: NoSuchBucketPolicy), o gap é
registrado em `snapshot.gaps` como `s3.<name>.Encryption: not collected`.
