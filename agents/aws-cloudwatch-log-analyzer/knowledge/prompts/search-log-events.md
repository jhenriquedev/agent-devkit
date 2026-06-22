# Prompt: Search Log Events

## Objetivo

Buscar eventos brutos em um log group com janela temporal e filtro opcional.

## Entradas

- `region`: regiao AWS.
- `log_group`: log group consultado.
- `start_time` e `end_time`: janela obrigatoria sem fixture.
- `filter_pattern`: filtro CloudWatch opcional.
- `log_stream_prefix`: restricao opcional por stream.
- `limit`: limite de eventos.

## Regras

- Exija escopo completo sem fixture.
- Use filtros e prefixos para reduzir volume sempre que possivel.
- Apresente eventos como evidencias, nao como conclusao final.
- Resuma mensagens longas e preserve apenas amostras controladas.
- Informe `next_token` quando houver paginacao.

## Saida

- Mostre consulta, janela, filtro, total e next token.
- Renderize amostras com timestamp, stream e mensagem resumida.
- Separe ausencia de eventos de erro de erro operacional.
- Indique lacunas se a janela ou stream parecer insuficiente.

## Nao faca

- Nao executar consulta sem janela.
- Nao despejar payloads completos.
- Nao escrever em AWS.
