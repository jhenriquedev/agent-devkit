# Update N2 Card Workflow

## Objetivo

Planejar ou executar acoes explicitas do fluxo N2 no Azure DevOps.

## Entradas

- `--project`, `--card`.
- `--target-state`, `--target-column`.
- `--assign-to`.
- `--execute`.

## Raciocinio

1. Monte tag N2.
2. Monte comentario tecnico.
3. Monte move-card quando houver estado alvo.
4. Inclua coluna quando houver estado e coluna.
5. Monte assign-card quando houver responsavel.
6. Monte attach-file quando houver patch plan.
7. Execute apenas com `--execute`.

## Rubrica/Regras

- `target-column` sozinho nao move card.
- `assign-to` exige usuario resolvivel pelo Azure.
- Sem execute, tudo fica planejado.

## Saida

JSON com `azureActions`, `targetState`, `targetColumn` e `assignTo`.

## Nao faca

- Nao sobrescrever card sem preview.
- Nao executar mutacao externa sem `--execute`.
