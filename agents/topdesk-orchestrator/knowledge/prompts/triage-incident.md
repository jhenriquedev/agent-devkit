# Triage Incident

## Objetivo

Sugerir categoria, prioridade e solicitante para um incidente TOPdesk usando
catalogos e pessoas conhecidas.

## Entradas

- `id` ou `number`.
- `execute`, `fixture`, `output`.

## Raciocinio

1. Leia o incidente e sua solicitacao.
2. Carregue catalogos de categorias e prioridades.
3. Busque pessoa correspondente ao solicitante.
4. Aplique `knowledge/triage-rules.md`.
5. Monte plano de update somente com campos sustentados por evidencia.

## Rubrica

- Sugestoes devem existir no catalogo.
- Prioridade deriva de impacto e urgencia.
- Caller exige correspondencia clara em persons.
- Sem evidencia, deixe campo fora do update.

## Saida

Fatos TOPdesk, inferencias do agente, payload de update e proxima acao.

## Nao faca

Nao sugerir valor fora do catalogo. Nao fechar, arquivar ou escalar. Nao aplicar
sem `--execute`.
