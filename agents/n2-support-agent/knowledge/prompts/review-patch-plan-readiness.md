# Review Patch Plan Readiness

## Objetivo

Bloquear ou liberar o patch plan para implementacao.

## Entradas

- Contrato `patchPlan`.
- Causa raiz.
- Analise de codigo.

## Raciocinio

1. Verifique se ha destino de entrega.
2. Verifique se ha card Azure ou contrato N1.
3. Verifique se ha arquivo candidato.
4. Verifique se a categoria nao e `insufficient_evidence`.
5. Verifique se a confianca e pelo menos 0.65.
6. Consolide blockers sem duplicar mensagens.

## Rubrica/Regras

- Qualquer blocker torna `readyForImplementation=false`.
- Baixa confianca bloqueia.
- Sem arquivo de codigo bloqueia.

## Saida

JSON com `readyForImplementation`, `blockers`, `rootCauseCategory` e
`confidence`.

## Nao faca

- Nao marcar ready com lacuna.
- Nao apagar blockers existentes.
