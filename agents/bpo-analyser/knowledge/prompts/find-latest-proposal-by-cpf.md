# Prompt: Find Latest BPO Proposal By CPF

## Objetivo

Encontrar a proposta mais recente/elegivel de um CPF segundo a regra do Core e
explicar o criterio de escolha.

## Entradas

- `--cpf` obrigatorio.
- `--format`, `--fixture` e `--output` opcionais.

## Raciocinio

1. Analise as propostas do CPF.
2. Filtre propostas integradas ou aprovadas (`INT`, `INTEGRADA`, `APR`,
   `APROVADA`) com `last_due_date`.
3. Ordene por `last_due_date` desc e selecione a primeira.
4. Reporte quantidade de origem e quantidade elegivel.

## Decisao

- Em producao, priorize `INT`; aceite `APR` como fallback analitico quando for o
  melhor candidato disponivel.
- Nenhuma proposta integrada/aprovada com `last_due_date` significa sem selecao.
- Nao consulte documentos nesta capability.

## Saida

CPF mascarado, criterio textual, total de origem, contagem de elegiveis e
proposta selecionada. Se nao houver selecao, explique o motivo.

## Nao faca

Nao exiba CPF completo. Nao amplie criterio sem ordem explicita. Nao chame API
SelfHire. Nao afirme que a proposta foi contratada.
