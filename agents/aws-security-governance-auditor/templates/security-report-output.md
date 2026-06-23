# AWS Security Governance Report — Contrato de Saída

> Fatos (fonte): dados coletados via AWS CLI allowlist ou --fixture.
> Inferências (agente): severidade e status atribuídos por `auditors.py`.

## Formato real emitido por `render_security_report` (report_renderer.py)

```
# AWS Security Governance Report

## Summary

- Findings: <N>
- critical: <N>
- high: <N>
- medium: <N>
- low: <N>
- info: <N>

## Findings

- [<severity>] <title> (<category>)
  - Resource: `<resource_id>`
  - Evidence: <evidence>
  - Recommendation: <recommendation>
```

## Campos obrigatórios por finding (finding_policy em policies.yaml)

`id`, `severity`, `category`, `resource_type`, `resource_id`, `title`, `evidence`, `recommendation`

## Artefatos gerados

- `security-report.md` — relatório humano (este formato)
- `security-findings.json` — payload `{ finding_count: N, findings: [...] }`

## Quality gates esperados

- `findings_have_severity`: todo finding tem severity em {critical,high,medium,low,info}
- `findings_have_evidence`: todo finding tem evidence não-vazio
- `secrets_redacted`: nenhum material sensível impresso
