# Update Azure Workflow

Planeja ou executa automacoes Azure de apoio ao N2. Mutacoes exigem `--execute`.

## Acoes

- Adiciona tag `Analise N2`.
- Gera comentario tecnico do N2.
- Anexa `patch_plan.md` quando houver arquivo de entrega.
- Move card quando `--target-state` for informado.
- Atualiza coluna quando `--target-state` e `--target-column` forem informados.
- Atribui responsavel quando `--assign-to` for informado.

Sem `--execute`, a saida fica como plano em `azureActions`. Com `--execute`,
cada action chama a capability correspondente do `azure-devops-orchestrator`.
