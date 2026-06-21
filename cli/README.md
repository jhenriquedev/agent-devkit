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
./ai-devkit run database-change-operator plan-migration --path migrations/202606211200_create_table.up.sql
./ai-devkit run postgres-data-analyzer list-tables --database outro_banco --schema public
./ai-devkit run sqlserver-data-analyzer list-tables --schema dbo
./ai-devkit run sqlserver-change-operator plan-migration --path migrations/001_create_table.up.sql
./ai-devkit run software-specification-analyst analyze-project-context --project . --output-dir specifications/contexto --yes-create-dir
./ai-devkit run software-specification-analyst create-complete-spec --input demanda.md
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

No `elasticsearch-log-analyzer`, as capabilities executaveis atuais sao:

- `list-log-sources`
- `search-log-events`
- `analyze-service-errors`
- `trace-request`
- `detect-error-patterns`
- `extract-log-samples`
- `generate-log-report`
- `correlate-azure-card-logs`

No `postgres-data-analyzer`, as capabilities executaveis atuais sao:

- `test-connection`
- `list-schemas`
- `list-tables`
- `describe-table`
- `run-readonly-query`
- `profile-table`
- `detect-sensitive-columns`
- `analyze-cpf-column`
- `generate-data-report`

No `database-change-operator`, as capabilities executaveis atuais sao:

- `test-write-permissions`
- `plan-migration`
- `apply-migration`
- `rollback-migration`
- `run-write-script`
- `upsert-records`
- `update-records`
- `migration-report`

No `sqlserver-data-analyzer`, as capabilities executaveis atuais sao:

- `test-connection`
- `list-databases`
- `list-schemas`
- `list-tables`
- `describe-table`
- `list-relationships`
- `suggest-joins`
- `search-tables`
- `search-columns`
- `explore-database-domain`
- `generate-erd-report`
- `run-readonly-query`
- `validate-readonly-query`
- `build-analysis-query`
- `explain-query-plan`
- `sample-table`
- `profile-table`
- `analyze-query-result`
- `detect-sensitive-columns`
- `detect-data-quality-issues`
- `analyze-cpf-column`
- `estimate-table-size`
- `compare-tables`
- `trace-record`
- `generate-data-report`

No `sqlserver-change-operator`, as capabilities executaveis atuais sao:

- `test-write-permissions`
- `plan-migration`
- `apply-migration`
- `rollback-migration`
- `run-write-script`
- `create-object`
- `update-records`
- `delete-records`
- `upsert-records`
- `backup-records`
- `change-report`

No `technical-integration-analyst`, as capabilities executaveis atuais sao:

- `ingest-technical-docs`
- `extract-integration-contract`
- `identify-missing-information`
- `analyze-integration-flow`
- `generate-test-data`
- `generate-http-artifacts`
- `generate-protocol-artifacts`
- `run-integration-tests`
- `generate-technical-docs`

No `software-specification-analyst`, as capabilities executaveis atuais sao:

- `analyze-project-context`
- `create-complete-spec`

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

Exemplo com documentacao tecnica de integracao:

```bash
./ai-devkit run technical-integration-analyst generate-http-artifacts --file api.md --postman-output /tmp/collection.json
```

Exemplo com Database Change Operator:

```bash
./ai-devkit run database-change-operator plan-migration --path migrations/202606211200_create_table.up.sql
./ai-devkit run database-change-operator apply-migration --path migrations/202606211200_create_table.up.sql --execute
```

Para banco de dados, escritas tambem rodam em dry-run por padrao. Use `--execute`
apenas depois de revisar o plano.

Exemplo com Software Specification Analyst:

```bash
./ai-devkit run software-specification-analyst analyze-project-context --project . --output-dir specifications/contexto --yes-create-dir
./ai-devkit run software-specification-analyst create-complete-spec --input demanda.md
```

Os runners propoem criar pastas em `specifications/<slug>/` no projeto atual e
perguntam antes de criar a pasta. Para automacao revisada, use
`--yes-create-dir`.

Exemplo multibanco com a mesma connection string base:

```bash
./ai-devkit run postgres-data-analyzer list-tables --database outro_banco --schema public
./ai-devkit run sqlserver-data-analyzer list-tables --database OutroBanco --schema dbo
```
./ai-devkit run database-change-operator migration-report --database outro_banco
```

O argumento `--database` troca somente o nome do database na URL Postgres. Host,
porta, usuario, senha e parametros como `sslmode` continuam vindo do `.env`.
