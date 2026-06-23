# IAM Audit — Contrato de Saída

> Fatos (fonte): IAM policies coletadas via `iam list-policies --scope Local` + `iam get-policy-version`.
> Inferências (agente): severidade determinística por `audit_iam_principals` (auditors.py).

## Formato real emitido por `render_findings` (report_renderer.py)

```
# IAM Audit

- [critical] IAM policy allows wildcard admin access - `<resource_id>`
  - Evidencia: Policy `<PolicyName>` contains Allow Action=* Resource=*.
  - Recomendacao: Replace wildcard permissions with least-privilege actions and scoped resources.
```

## Artefatos gerados

- `iam-audit.json` — `{ account_id, region, audit: "iam", finding_count: N, findings: [...] }`
- `iam-audit.md` — relatório humano

## LACUNA DE COLETA

Se `snapshot.iam.policies` estiver vazio (coleta falhou ou sem políticas locais),
reportar LACUNA em vez de "IAM seguro".
