# Workflow: Extract Log Samples

## Objetivo

Extrair amostras representativas de logs sem despejar grandes volumes.

## Passos

1. Validar escopo.
2. Buscar eventos.
3. Aplicar estrategia de amostragem.
4. Renderizar amostras selecionadas.

## Guardrails

- Respeitar `sample_size`.
- Resumir mensagens longas.
- Nao transformar amostra em conclusao.
