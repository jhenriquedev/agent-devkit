# CLI

Interface de linha de comando do AI DevKit.

## Objetivo

Fornecer comandos curtos e unificados para descobrir agentes, listar
capabilities e inspecionar contratos sem navegar manualmente pela estrutura de
arquivos.

O executavel fica na raiz do repositorio:

```bash
./ai-devkit <comando>
python ai-devkit <comando>
```

## Comandos MVP

```bash
./ai-devkit agents
./ai-devkit capabilities azure-devops-orchestrator
./ai-devkit inspect azure-devops-orchestrator read-card
./ai-devkit run azure-devops-orchestrator read-card --project "Projeto" --id 123 --include-comments
./ai-devkit run topdesk-orchestrator read-incident --number "I 2606 001"
```

Aliases:

```bash
./ai-devkit a
./ai-devkit c azure-devops-orchestrator
./ai-devkit i azure-devops-orchestrator read-card
./ai-devkit r azure-devops-orchestrator read-card --project "Projeto" --id 123
```

Use `--json` para saida estruturada:

```bash
./ai-devkit --json inspect azure-devops-orchestrator read-card
```

## Execucao

O comando `run` delega para o `runner.py` declarado no `capability.yaml`.
Apenas capabilities com `entrypoint.runner` sao executaveis pela CLI. As demais
podem ser inspecionadas e usadas por agentes consumidores como contratos
declarativos.

No `azure-devops-orchestrator`, as capabilities executaveis atuais sao:

- `list-cards`
- `read-card`
- `comment-card`
- `update-card-tags`
- `assign-card`
- `move-card`
- `prepare-card-analysis`
- `generate-cards-report`

No `aws-cloudwatch-log-analyzer`, as capabilities executaveis atuais sao:

- `list-log-groups`
- `search-log-events`
- `analyze-service-error`
- `trace-request`
- `detect-error-patterns`
- `extract-log-samples`
- `generate-incident-report`
- `correlate-azure-card-logs`

No `topdesk-orchestrator`, as capabilities executaveis atuais sao:

- `list-incidents`
- `read-incident`
- `create-incident`
- `update-incident`
- `analyze-incident-insufficiency`
- `request-more-info`
- `incident-report`

Exemplo com fixture local:

```bash
./ai-devkit run azure-devops-orchestrator read-card --fixture /tmp/card.json --include-comments
```

Exemplo com Azure DevOps real, usando `.env` da raiz:

```bash
./ai-devkit run azure-devops-orchestrator read-card --project "Projeto" --id 123 --include-comments
```

Para Azure DevOps, sempre prefira informar `--project` no comando. Isso evita
fixar o agente a um unico projeto e permite usar a mesma organizacao/token para
varios projetos.

Exemplo com TOPdesk real, usando `.env` da raiz:

```bash
./ai-devkit run topdesk-orchestrator read-incident --number "I 2606 001" --include-progress-trail
```

Para TOPdesk, escritas como `create-incident`, `update-incident` e
`request-more-info` rodam em dry-run por padrao. Use `--execute` apenas quando a
alteracao estiver revisada.
