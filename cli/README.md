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
./ai-devkit inspect azure-devops-orchestrator ler-card
./ai-devkit run azure-devops-orchestrator ler-card --project "Projeto" --id 123 --include-comments
```

Aliases:

```bash
./ai-devkit a
./ai-devkit c azure-devops-orchestrator
./ai-devkit i azure-devops-orchestrator ler-card
./ai-devkit r azure-devops-orchestrator ler-card --project "Projeto" --id 123
```

Use `--json` para saida estruturada:

```bash
./ai-devkit --json inspect azure-devops-orchestrator ler-card
```

## Execucao

O comando `run` delega para o `runner.py` declarado no `capability.yaml`.
Apenas capabilities com `entrypoint.runner` sao executaveis pela CLI. As demais
podem ser inspecionadas e usadas por agentes consumidores como contratos
declarativos.

Exemplo com fixture local:

```bash
./ai-devkit run azure-devops-orchestrator ler-card --fixture /tmp/card.json --include-comments
```

Exemplo com Azure DevOps real, usando `.env` da raiz:

```bash
./ai-devkit run azure-devops-orchestrator ler-card --project "Projeto" --id 123 --include-comments
```

Para Azure DevOps, sempre prefira informar `--project` no comando. Isso evita
fixar o agente a um unico projeto e permite usar a mesma organizacao/token para
varios projetos.
