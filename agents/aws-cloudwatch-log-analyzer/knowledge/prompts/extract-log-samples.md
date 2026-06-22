# Prompt: Extract Log Samples

## Objetivo

Extrair amostras pequenas e representativas de logs para analise humana ou
anexo operacional.

## Entradas

- `region`, `log_group`, `start_time`, `end_time`: escopo dos eventos.
- `sample_strategy`: first, error-first ou spread.
- `sample_size`: quantidade desejada de amostras.
- `filter_pattern`, `log_stream_prefix` e `limit`: refinamento opcional.

## Regras

- Respeite `sample_size`.
- Priorize mensagens de erro quando a estrategia pedir `error-first`.
- Use distribuicao temporal quando a estrategia pedir `spread`.
- Resuma mensagens longas.
- Explique que amostra nao equivale a conclusao.

## Saida

- Mostre estrategia, tamanho solicitado e tamanho retornado.
- Renderize tabela de amostras.
- Informe criterio de selecao aplicado.
- Liste lacunas quando a amostra for pequena demais.

## Nao faca

- Nao despejar todos os logs.
- Nao transformar amostra em causa raiz.
- Nao incluir dados sensiveis sem mascaramento.
