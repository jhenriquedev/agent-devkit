# Prompt: List Log Groups

## Objetivo

Descobrir log groups de forma controlada para orientar consultas posteriores no
CloudWatch Logs.

## Entradas

- `region`: regiao AWS obrigatoria sem fixture.
- `log_group_prefix`: prefixo para restringir descoberta.
- `service` e `environment`: contexto humano opcional.
- `limit`: limite maximo de grupos retornados.

## Regras

- Use esta capability apenas para descoberta de log groups.
- Se nao houver prefixo, destaque que a consulta pode ser ampla.
- Nao inferir saude do servico pela existencia ou ausencia de um log group.
- Prefira prefixos como `/aws/`, nome do servico ou caminho conhecido.
- Trate nomes de log groups como dados operacionais sensiveis.

## Saida

- Informe regiao, prefixo, servico, ambiente, limite e total retornado.
- Renderize tabela com log group, retention e bytes armazenados.
- Inclua aviso quando o prefixo nao foi informado.
- Sugira proximo passo somente se o usuario pediu investigacao.

## Nao faca

- Nao consultar eventos.
- Nao varrer regioes automaticamente.
- Nao criar, alterar ou apagar log groups.
