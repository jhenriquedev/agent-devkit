# Prompt: List Log Streams

## Objetivo

Listar streams de um log group CloudWatch para restringir consultas futuras por
origem, task, instancia ou periodo.

## Entradas

- `region`: regiao AWS.
- `log_group`: log group consultado.
- `log_stream_prefix`: prefixo opcional para reduzir a listagem.
- `limit`: limite maximo de streams.

## Regras

- Use esta capability para descoberta de streams, nao para analise de mensagens.
- Exija `region` e `log_group` sem fixture.
- Aplique prefixo quando houver pista de servico, data, task ou instancia.
- Trate ausencia de streams como fato do escopo consultado.
- Nao inferir disponibilidade do servico apenas pela listagem.

## Saida

- Mostre regiao, log group, prefixo, limite e total retornado.
- Renderize tabela com stream, ultimo evento e bytes armazenados.
- Avise quando nenhum prefixo for usado.
- Sugira `search-log-events` quando a proxima etapa for ler mensagens.

## Nao faca

- Nao consultar eventos.
- Nao listar todas as regioes.
- Nao escrever em AWS.
