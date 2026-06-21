# TOPdesk Integration

Integracao local com TOPdesk API.

## Configuracao

```text
TOPDESK_BASE_URL=https://tenant.topdesk.net
TOPDESK_USERNAME=integration-user
TOPDESK_APP_PASSWORD=application-password
```

## CLI interna

```bash
python agents/topdesk-orchestrator/infra/integrations/topdesk/cli.py list-incidents --limit 10
python agents/topdesk-orchestrator/infra/integrations/topdesk/cli.py get-incident --number "I 2506 123"
```
