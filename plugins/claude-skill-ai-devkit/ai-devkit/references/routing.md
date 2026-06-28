# Routing

Prefer the narrowest matching agent and capability.

- Incidents, cards, customer symptoms: `n1-support-agent`, then `n2-support-agent`.
- AWS architecture: `aws-architecture-analyst`.
- AWS operational action: `aws-operations-operator`.
- AWS logs: `aws-cloudwatch-log-analyzer`.
- Elasticsearch logs: `elasticsearch-log-analyzer`.
- Azure DevOps cards: `azure-devops-orchestrator`.
- TOPdesk incidents: `topdesk-orchestrator`.
- SQL Server analysis: `sqlserver-data-analyzer`.
- SQL Server changes: `sqlserver-change-operator`.
- Postgres analysis: `postgres-data-analyzer`.
- Database changes: `database-change-operator`.
- Technical contracts: `technical-integration-analyst`.
- Software specs: `software-specification-analyst`.
- Figma/product UI: `figma-ui-ux-product-designer`.
- Excel: `excel-workbook-builder`.
- Presentations: `presentation-deck-builder`.
- Diagrams: `drawio-diagram-builder`.
- Knowledge generation: `knowledge-generator`.

When local runtime is available, inspect with:

```bash
agent agents list --json
agent capabilities list --agent <agent> --json
agent inspect <agent> <capability> --json
```
