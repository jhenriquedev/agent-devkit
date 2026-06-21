# Workflow: Correlate Azure Card Logs

## Objetivo

Correlacionar dados de um card Azure DevOps com eventos CloudWatch.

## Passos

1. Validar dados do card ou fixture.
2. Resolver log group e janela de tempo.
3. Buscar eventos CloudWatch.
4. Separar dados do card de dados dos logs.
5. Gerar analise complementar.

## Guardrails

- Nao escrever no Azure.
- Nao escrever na AWS.
- Nao assumir log group se nao existir no card ou entrada.
