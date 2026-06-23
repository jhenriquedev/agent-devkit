# Prompt: Trace Request

## Objetivo
Rastrear uma única request ao longo dos logs por identificador (trace, correlation,
request, user ou custom) e montar uma timeline concisa.

## Entradas esperadas
- Obrigatórias: `--source`, `--request-id`, `--from`, `--to`.
- Opcionais: `--service`, `--environment`, `--time-field`, `--limit`.

## Raciocínio
1. Não assuma um único campo de id: a busca cobre `<id>` livre OR trace.id OR trace_id OR
   correlation_id OR request_id.
2. Ordene os eventos por timestamp (timeline crescente).
3. Procure gaps temporais ou mudança de serviço que indiquem o ponto de falha.

## Regras de decisão
- Mantenha o identificador pedido visível no output. Ver também: decision-rules.md.
- Se zero eventos: recomende alargar a janela ou trocar o source pattern (não invente trace).
- Se o id aparecer em serviços distintos, mostre a transição (entrada -> saída).

## Formato de saída
Cabeçalho (source/request id/contagem) + tabela "Timeline" ordenada por tempo + recomendação se vazio.

## Não fazer
- Não fixar um campo de trace específico sem evidência do mapping.
- Não truncar o id no output.
