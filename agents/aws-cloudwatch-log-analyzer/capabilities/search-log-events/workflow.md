# Workflow: Search Log Events

## Objetivo

Buscar eventos em um log group com janela de tempo e filtro opcional.

## Passos

1. Validar escopo: `region`, `log_group`, `start_time`, `end_time`.
2. Executar `filter_log_events`.
3. Renderizar contagem, janela e amostras.
4. Sinalizar `next_token` quando existir.

## Guardrails

- Nao executar busca sem janela de tempo.
- Aplicar limite.
- Resumir mensagens longas.
