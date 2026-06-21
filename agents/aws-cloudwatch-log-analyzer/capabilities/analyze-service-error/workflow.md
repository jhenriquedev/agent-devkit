# Workflow: Analyze Service Error

## Objetivo

Analisar eventos de erro de um servico em uma janela de tempo.

## Passos

1. Validar servico, ambiente e escopo CloudWatch.
2. Buscar eventos com filtro de erro.
3. Separar eventos de erro.
4. Agrupar mensagens, status codes e endpoints.
5. Gerar hipoteses e proximos passos.

## Guardrails

- Separar fatos de hipoteses.
- Nao afirmar causa raiz sem evidencia.
- Resumir payloads grandes.
