# Azure Integration

Integracao executavel com Azure DevOps Boards.

## Objetivo

Conectar no Azure DevOps usando variaveis de ambiente da raiz e expor um
repository local que retorna JSON estruturado para as capabilities do agente.

## Estrutura

```text
azure/
├─ integration.yaml
├─ azure_repository.py
├─ cli.py
├─ env.example
├─ methods/
├─ models/
└─ mcp/
```

- `azure_repository.py`: repository Python sem dependencias externas.
- `cli.py`: entrada de linha de comando para agentes e humanos.
- `methods/`: contratos dos metodos expostos pelo repository.
- `models/`: schemas JSON dos dados retornados.
- `mcp/`: placeholder para uma futura exposicao MCP dos mesmos methods.

## Execucao local

O repository usa apenas biblioteca padrao do Python e carrega automaticamente o
primeiro `.env` encontrado subindo a partir do diretorio atual ou desta
integracao. `AZURE_DEVOPS_ORG` e `AZURE_DEVOPS_PAT` sao globais; o projeto deve
ser passado por comando com `--project`. `AZURE_DEVOPS_PROJECT` pode existir
apenas como fallback local.

Exemplos:

```bash
python agents/azure-devops-orchestrator/infra/integrations/azure/cli.py get-work-item --project "Projeto" --id 123
python agents/azure-devops-orchestrator/infra/integrations/azure/cli.py list-work-items --project "Projeto" --state Active
python agents/azure-devops-orchestrator/infra/integrations/azure/cli.py add-comment --project "Projeto" --id 123 --comment "Comentario" --execute
```

Sem `--execute`, metodos de escrita rodam como dry-run.

Para validar o comportamento completo de uma capability, prefira a CLI raiz:

```bash
agent run azure-devops-orchestrator read-card --project "Projeto" --id 123 --include-comments
```

O repository normaliza work items com campos como `id`, `work_item_type`,
`title`, `state`, `created_date`, `changed_date`, `board_column`,
`board_column_done`, `assigned_to`, `tags`, `description`,
`acceptance_criteria`, `relations` e `url`.

## Regras

- Credenciais devem vir do `.env` da raiz ou do ambiente de execucao.
- Nunca commitar tokens ou respostas reais contendo dados sensiveis.
- Metodos de escrita devem implementar dry-run ou confirmacao antes da execucao.
- Validar estados, tags e usuarios antes de alterar work items.
