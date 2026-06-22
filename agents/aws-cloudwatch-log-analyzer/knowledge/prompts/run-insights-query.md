# Prompt: Run Insights Query

## Objetivo

Iniciar ou consultar uma query CloudWatch Logs Insights para investigacao
agregada e somente leitura.

## Entradas

- `region`: regiao AWS.
- `log_group`: log group para iniciar uma query.
- `start_time` e `end_time`: janela temporal obrigatoria para iniciar.
- `query`: query Logs Insights.
- `query_id`: identificador para consultar resultado de query ja iniciada.
- `limit`: limite de resultados.

## Regras

- Se `query_id` existir, consulte resultados e nao inicie nova query.
- Sem `query_id`, exija regiao, log group, janela e query.
- Prefira queries agregadas, com filtros e limite baixo para triagem.
- Nao fazer polling infinito; retorne query id quando a query foi iniciada.
- Separe resultados observados de hipoteses.

## Saida

- Mostre escopo, query id, status e query quando fornecida.
- Para query iniciada, oriente consultar novamente por `query_id`.
- Para resultados, renderize linhas resumidas e estatisticas.
- Inclua guardrail de dados sensiveis e nenhuma escrita.

## Nao faca

- Nao executar query sem janela temporal.
- Nao usar query ampla em log group desconhecido.
- Nao afirmar causa raiz apenas por resultado agregado.
