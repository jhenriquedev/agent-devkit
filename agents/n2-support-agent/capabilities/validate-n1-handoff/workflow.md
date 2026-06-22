# Validate N1 Handoff

## Fluxo

1. Carregar o contexto N2.
2. Verificar se o contrato N1 existe.
3. Conferir `entities`, `checks`, `decision` e `diagnosticGaps`.
4. Copiar gaps abertos para `openDiagnosticGaps`.
5. Marcar `needsN1Rerun` quando faltar evidencia ou houver gap aberto.
6. Retornar entidades mascaradas para continuidade.

## Saida

Retorna contrato de suficiencia do handoff N1.
