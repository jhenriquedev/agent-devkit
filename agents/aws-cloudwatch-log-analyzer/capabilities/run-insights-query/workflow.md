# Workflow: Run Insights Query

## Objetivo

Iniciar uma query CloudWatch Logs Insights ou consultar resultados por `query_id`.

## Passos

1. Se `query_id` foi informado, executar `get_logs_insights_query_results`.
2. Caso contrario, validar `region`, `log_group`, `start_time`, `end_time` e `query`.
3. Executar `start_logs_insights_query` com limite explicito.
4. Renderizar `query_id`, status, resultados disponiveis e estatisticas.

## Guardrails

- Nao executar query sem janela temporal.
- Nao usar query ampla sem log group explicito.
- Nao fazer polling infinito; consultar resultados por `query_id`.
- Tratar resultados como dados sensiveis.
