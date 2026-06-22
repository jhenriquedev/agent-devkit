# Select Specialist Checks

## Objetivo

Escolher validacoes especialistas para confirmar ou descartar a hipotese N2.

## Entradas

- Contexto N2.
- Handoff N1.
- Categoria de causa raiz candidata.
- Catalogo `knowledge/runbooks/specialist-validation-catalog.md`.

## Raciocinio

1. Se o handoff N1 estiver incompleto ou com gaps, selecione N1.
2. Se houver proposta, BPO ou documento, selecione BPO.
3. Se houver erro runtime ou backend bug, selecione logs.
4. Se houver backend bug ou inconsistencia, selecione banco read-only.
5. Nao selecione operadores de mutacao como validacao.

## Rubrica/Regras

- Validacao deve ter agente e capability existentes.
- Se a execucao depender de parametros ausentes, ela sera pulada com lacuna.
- Banco/logs exigem contrato seguro antes de executar.

## Saida

JSON com `selectedChecks`, cada item contendo `agent`, `capability` e `reason`.

## Nao faca

- Nao executar validacao nesta etapa.
- Nao escolher operador de escrita.
- Nao passar CPF mascarado como parametro.
