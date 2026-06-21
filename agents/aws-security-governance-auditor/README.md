# AWS Security Governance Auditor

Agente especialista em auditoria AWS read-only para seguranca e governanca.

## Capabilities

```bash
./ai-devkit capabilities aws-security-governance-auditor
./ai-devkit run aws-security-governance-auditor audit-iam-principals --profile dev --region us-east-1 --output-dir aws-security --yes-create-dir
./ai-devkit run aws-security-governance-auditor generate-security-report --audit-dir aws-security --output-dir aws-security --yes-overwrite
./ai-devkit run aws-security-governance-auditor generate-remediation-plan --audit-dir aws-security --output-dir aws-security --yes-overwrite
```

## Guardrails

- Read-only no MVP.
- Remediacoes sao planos, nunca execucao.
- Secrets e policies completas nao devem aparecer em relatorios humanos.
