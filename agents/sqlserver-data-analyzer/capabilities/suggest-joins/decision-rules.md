# Decision Rules: suggest-joins

## Rubrica de confiança de join

| Condição | Confiança | Ação do host |
|---|---|---|
| Join vem de FK declarada (constraint real) | `high` | Pode ser usado diretamente em queries |
| Join vem de heurística de nome (sufixo `_id`, normalização de nome de coluna) | `medium` | Deve ser validado pelo usuário antes de produção |

## Regras de decisão

1. Separar SEMPRE sugestões `high` de `medium` na resposta.
2. Para cada sugestão `medium`, incluir aviso explícito: "inferência por padrão
   de nome — valide antes de usar em produção."
3. Se `count == 0`: não há FK nem heurística óbvia. Sugerir `describe-table`
   para inspecionar colunas manualmente e `list-relationships` para confirmar.
4. Não apresentar heurística como verdade confirmada; nunca omitir o label
   `confidence`.

## Quando escalar / pedir info

- Schema desconhecido → sugerir `list-schemas` primeiro.
- FK retornou apenas heurística e o usuário quer certeza → sugerir
  `list-relationships` para confirmar FK real.
