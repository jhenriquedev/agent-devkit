# Workflow: Ler Card

## Objetivo

Ler um card e transformar os dados em uma analise objetiva para decisao.

## Execucao local

```bash
./ai-devkit run azure-devops-orchestrator ler-card --project <project> --id <work-item-id> --include-comments
```

Para testes sem Azure DevOps real:

```bash
./ai-devkit run azure-devops-orchestrator ler-card --fixture <fixture.json> --include-comments
```

## Passos

1. Validar o projeto e o ID do work item.
2. Executar `get-work-item` com `expand_relations=true`.
3. Se solicitado ou relevante, executar `get-work-item-comments`.
4. Separar fatos da API de inferencias do agente.
5. Reportar ID, tipo, titulo, status, coluna, datas, responsavel, tags,
   anexos, comentarios e URL.
6. Identificar lacunas, riscos, bloqueios e proximos passos.
7. Responder usando `../../templates/ler-card-output.md`.

## Guardrails

- Nao alterar o card.
- Nao assumir criterios de aceite ausentes.
- Nao inferir responsavel real por nome parcial.
- Se houver comentarios conflitantes, sinalizar conflito.
- Se a descricao incluir logs com dados sensiveis, resumir o payload na resposta
  humana em vez de reproduzir o bloco bruto.
