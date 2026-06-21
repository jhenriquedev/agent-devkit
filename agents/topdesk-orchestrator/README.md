# TOPdesk Orchestrator

Agente especialista para operar TOPdesk via API, inspirado no padrao do
`azure-devops-orchestrator`.

## Escopo inicial

O MVP cobre incidentes:

- listar incidentes;
- ler incidente por ID ou numero;
- ler progress trail;
- criar incidente;
- atualizar campos controlados;
- analisar chamados com pouco insumo;
- gerar pedido de mais informacoes;
- gerar relatorio operacional de incidentes.

## Como usar

```bash
./ai-devkit run topdesk-orchestrator list-incidents --limit 20
./ai-devkit run topdesk-orchestrator read-incident --number "I 2506 123"
./ai-devkit run topdesk-orchestrator create-incident --brief-description "Erro no sistema" --request "Usuario informa erro ao acessar."
./ai-devkit run topdesk-orchestrator update-incident --id <id> --fields-json '{"briefDescription":"Novo resumo"}'
./ai-devkit run topdesk-orchestrator analyze-incident-insufficiency --fixture /tmp/incident.json
./ai-devkit run topdesk-orchestrator request-more-info --id <id>
./ai-devkit run topdesk-orchestrator incident-report --fixture /tmp/incidents.json
```

Escritas reais exigem `--execute`.

## Configuracao

Credenciais devem vir do `.env` da raiz ou do ambiente:

- `TOPDESK_BASE_URL`
- `TOPDESK_USERNAME`
- `TOPDESK_APP_PASSWORD`

`TOPDESK_PASSWORD` tambem e aceito como fallback local para compatibilidade.
