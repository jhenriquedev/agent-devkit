# Prompt: Search Log Events

## Objetivo
Buscar eventos de log dentro de um escopo de runtime explícito e resumir os eventos
retornados, sem alterar estado externo.

## Entradas esperadas
- Obrigatórias: `--source`, `--from`, `--to`.
- Opcionais: `--query`, `--service`, `--environment`, `--level`, `--filters-json`,
  `--time-field`, `--limit` (default 100, máx 1000).

## Raciocínio
1. Confirme source + janela. Se faltar, peça ao usuário antes de executar.
2. Prefira filtros estruturados (service/environment/level/filters) a `--query` texto livre.
3. Use `count` para dimensionar o volume; só então decida o `--limit` das amostras.
4. Resuma: escopo, total de matches, e a tabela de eventos (time/service/level/trace/message/id).

## Regras de decisão
- Nunca busque sem janela de tempo (range obrigatório). Ver também: decision-rules.md.
- Nunca retorne eventos ilimitados; respeite `default_events=100`, `max_events=1000`.
- Se `total` >> `limit`, avise que a amostra é parcial e sugira estreitar filtros.

## Formato de saída
Bloco "Scope" (source/from/to/service/environment/level/query/total) + tabela "Events".

## Não fazer
- Não combine janelas implícitas; sempre explicite from/to no output.
- Não imprima credenciais ou o header Authorization.
