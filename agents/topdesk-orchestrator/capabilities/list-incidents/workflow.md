# List Incidents Workflow

## Fluxo

1. Receber filtros `query`, `status`, `operator_group` e `limit`.
2. Carregar fixture quando informada.
3. Sem fixture, chamar `TopdeskRepository.list_incidents`.
4. Renderizar filtros efetivos.
5. Renderizar tabela com ID, numero, resumo, status, prioridade e grupo.
6. Quando nao houver itens, renderizar linha vazia padronizada.
7. Nao executar qualquer escrita.

## Saida

Retorna `incidents-list.md`.
