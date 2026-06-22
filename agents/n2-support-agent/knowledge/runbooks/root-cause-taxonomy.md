# Taxonomia de Causa Raiz N2

## Objetivo

Padronizar a classificacao de causa raiz usada pelo `classify-root-cause` e pelo
`patch_plan.md`.

## Categorias

- `backend_bug`: ha erro, excecao, falha de regra ou fluxo backend com arquivo de
  codigo candidato localizado.
- `data_inconsistency`: ha divergencia de estado entre banco, sistemas ou
  persistencia.
- `external_provider_issue`: a evidencia aponta para sistema externo, BPO,
  provider ou fornecedor como origem provavel.
- `customer_pending_action`: o fluxo depende de acao documental, aceite,
  formalizacao ou dado pendente do cliente.
- `insufficient_evidence`: faltam codigo candidato, evidencia runtime ou handoff
  suficiente para causa raiz segura.

## Limiar

`readyForImplementation` so pode ser verdadeiro quando a confianca for maior ou
igual a `0.65` e a categoria nao for `insufficient_evidence`.

## Rubrica

- Erro backend + codigo localizado: `backend_bug`, confianca base `0.78`.
- Divergencia de banco/estado: `data_inconsistency`, confianca base `0.74`.
- BPO/provider/documento pendente sem sinal de bug: `external_provider_issue` ou
  `customer_pending_action`, confianca base `0.72`.
- Sem codigo localizado: `insufficient_evidence`, confianca abaixo de `0.65`.
