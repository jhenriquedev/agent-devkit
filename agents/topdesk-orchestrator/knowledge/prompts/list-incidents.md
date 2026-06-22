# List Incidents

## Objetivo

Listar incidentes TOPdesk por filtros simples e resumir o panorama operacional.

## Entradas

- `query`, `status`, `operator_group`, `limit`.
- `fixture` para execucao offline.

## Raciocinio

1. Confirme os filtros recebidos.
2. Traduza linguagem natural para filtros suportados sem inventar escopo.
3. Execute `list-incidents`.
4. Conte total retornado e observe concentracao por status ou grupo.
5. Marque chamados sem grupo ou prioridade como candidatos a triagem.

## Rubrica

- A lista e amostra quando houver `limit`.
- Nao trate retorno limitado como populacao completa.
- Fatos sao os campos retornados pelo TOPdesk.

## Saida

Tabela com ID, numero, resumo, status, prioridade e grupo, seguida de observacoes
curtas quando houver risco operacional evidente.

## Nao faca

Nao altere incidentes. Nao classifique prioridade aqui. Nao pagine alem de
`limit` sem pedido explicito.
