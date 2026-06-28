# AWS Architecture Analyst

Agente especialista em analise arquitetural AWS em modo read-only.

## Capabilities

```bash
agent capabilities aws-architecture-analyst
agent run aws-architecture-analyst discover-account-inventory --profile dev --region us-east-1 --output-dir aws-analysis --yes-create-dir
agent run aws-architecture-analyst map-service-dependencies --inventory aws-analysis/inventory.json --output-dir aws-analysis --yes-overwrite
agent run aws-architecture-analyst generate-architecture-report --inventory aws-analysis/inventory.json --dependency-map aws-analysis/dependency-map.json --output-dir aws-analysis --yes-overwrite
```

## Guardrails

- O agente nao altera recursos AWS.
- O repository bloqueia comandos fora da allowlist.
- Artefatos locais exigem `--yes-create-dir` quando o diretorio nao existe.
- Relatorios separam fatos, inferencias e lacunas.
