# Prompt: Analyze Service Error

## Objetivo

Analisar erros de um servico em uma janela CloudWatch e transformar eventos em
evidencias operacionais.

## Entradas

- `service`: servico investigado.
- `environment`: ambiente como prd, hml ou dev.
- `region`, `log_group`, `start_time`, `end_time`: escopo CloudWatch.
- `filter_pattern` e `limit`: refinamento opcional.

## Regras

- Classifique como fato apenas o que apareceu nos logs consultados.
- Agrupe mensagens, status codes e endpoints quando houver repeticao.
- Declare hipoteses com linguagem condicional.
- Nao afirmar causa raiz sem evidencias convergentes.
- Resuma stack traces e payloads grandes.

## Saida

- Mostre sumario de servico, ambiente, total e erros.
- Liste padroes com contagem.
- Apresente hipoteses e proximos passos de validacao.
- Inclua lacunas quando faltarem logs, correlacao ou contexto de deploy.

## Nao faca

- Nao mover incidente ou card.
- Nao culpar componente sem evidencia.
- Nao expor segredos de log.
