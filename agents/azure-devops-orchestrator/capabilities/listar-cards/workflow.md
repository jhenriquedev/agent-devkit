# Workflow: Listar Cards

## Objetivo

Listar cards do Azure DevOps com filtros claros e resposta estruturada.

## Passos

1. Confirmar projeto e criterio de busca.
2. Se o usuario nao fornecer query, pedir ou inferir filtro minimo seguro.
3. Executar `list-work-items`.
4. Apresentar resultados com ID, titulo, tipo, estado, responsavel e tags.
5. Destacar ambiguidades, limite aplicado e proximos passos possiveis.

## Saida esperada

Use `../../templates/listar-cards-output.md`.

## Guardrails

- Nao listar volume ilimitado; aplicar limite padrao quando nao informado.
- Nao executar escrita.
- Nao inferir prioridade sem campo ou regra explicita.
