# Workflow: Gerar Relatorio Cards

## Objetivo

Gerar um relatorio consolidado de cards Azure DevOps usando filtros de listagem
e leitura detalhada dos work items retornados.

## Execucao local

```bash
./ai-devkit run azure-devops-orchestrator generate-cards-report --project <project> --state "To Do" --limit 50 --include-comments
```

Com fixture:

```bash
./ai-devkit run azure-devops-orchestrator generate-cards-report --fixture <fixture.json>
```

## Passos

1. Validar projeto ou fixture.
2. Executar `list-work-items` com os filtros informados.
3. Para cada ID retornado, executar `get-work-item` com relations.
4. Se solicitado, executar `get-work-item-comments`.
5. Calcular sumario executivo e lacunas operacionais.
6. Renderizar tabela consolidada.
7. Renderizar detalhes por card quando `--include-details` estiver habilitado.
8. Gravar no stdout ou em `--output`.

## Guardrails

- Nao executar escrita.
- Respeitar `limit`.
- Avisar quando o retorno atingir o limite.
- Nao inferir prioridade sem campo ou tag explicita.
- Resumir descricoes longas nos detalhes.
