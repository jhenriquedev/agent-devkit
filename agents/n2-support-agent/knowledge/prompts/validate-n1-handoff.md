# Validate N1 Handoff

## Objetivo

Decidir se o contrato N1 sustenta uma investigacao N2.

## Entradas

- Contrato N1 vindo de arquivo, fixture ou contexto carregado.
- Campos esperados: `entities`, `checks`, `decision`, `diagnosticGaps`.

## Raciocinio

1. Verifique se o contrato N1 existe.
2. Confira a presenca de `entities`, `checks`, `decision` e `diagnosticGaps`.
3. Copie gaps abertos para `openDiagnosticGaps`.
4. Se houver chave ausente, marque handoff insuficiente.
5. Se houver gap aberto, recomende re-rodar ou complementar N1.
6. Preserve entidades mascaradas para as proximas etapas.

## Rubrica/Regras

- Sem contrato: `accepted=false`.
- Chave obrigatoria ausente: `accepted=false`.
- Gap aberto: `accepted=false` e `needsN1Rerun=true`.
- Sem lacuna: `accepted=true`.

## Saida

JSON com `accepted`, `missingRequiredEvidence`, `openDiagnosticGaps`,
`n1ContractLoaded`, `entities` e `needsN1Rerun`.

## Nao faca

- Nao invente evidencias N1.
- Nao ignore diagnostic gaps.
- Nao conclua causa raiz neste passo.
