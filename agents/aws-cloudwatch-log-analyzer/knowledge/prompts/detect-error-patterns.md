# Prompt: Detect Error Patterns

## Objetivo

Detectar recorrencia de erros agrupando eventos por dimensao operacional.

## Entradas

- `region`, `log_group`, `start_time`, `end_time`: escopo dos logs.
- `group_by`: message, status_code, endpoint ou stream.
- `filter_pattern`, `log_stream_prefix` e `limit`: refinamento opcional.

## Regras

- Filtre eventos de erro antes de agrupar quando a entrada trouxer eventos mistos.
- Use normalizacao de mensagem para reduzir ids e numeros variaveis.
- Nao mesclar padroes semanticamente diferentes apenas por semelhanca textual.
- Apresente contagens e exemplos curtos.
- Trate baixa amostragem como lacuna.

## Saida

- Mostre consulta e criterio de agrupamento.
- Liste padroes ordenados por frequencia.
- Inclua exemplos representativos.
- Sugira investigacao complementar quando um padrao dominar a amostra.

## Nao faca

- Nao afirmar impacto de negocio por frequencia isolada.
- Nao expandir a janela automaticamente.
- Nao expor payload completo.
