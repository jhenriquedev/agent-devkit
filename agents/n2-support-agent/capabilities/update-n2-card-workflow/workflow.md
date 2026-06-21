# Update N2 Card Workflow

Planeja ou executa automacoes Azure explicitas para o fluxo N2.

## Entradas

- `--project`: projeto Azure DevOps.
- `--card`: ID do work item.
- `--target-state`: estado alvo para `move-card`.
- `--target-column`: coluna alvo para `move-card`.
- `--assign-to`: responsavel alvo para `assign-card`.
- `--execute`: executa as acoes no Azure.
- `--format json`: retorna contrato estruturado.

## Comportamento

Sem `--execute`, a capability monta o plano de acoes em `azureActions` e inclui
`commandPreview` para cada automacao executavel. Com `--execute`, ela chama o
`azure-devops-orchestrator` para aplicar tag, comentario, movimentacao,
atribuicao e anexo quando os parametros forem suficientes.

`--target-column` sozinho nao executa movimento, porque a capability
`move-card` exige `--target-state`. Nesse caso a acao volta como `skipped`,
deixando a lacuna explicita no contrato.

## Acoes geradas

- `update-card-tags`: adiciona `Analise N2`.
- `comment-card`: registra resumo tecnico N2.
- `move-card`: altera estado e coluna quando `--target-state` existe.
- `assign-card`: atribui responsavel quando `--assign-to` existe.
- `attach-file`: anexa `patch_plan.md` quando existe arquivo gerado.
