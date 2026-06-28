# Decision Rules: List Relationships

- Listar relacionamentos por FKs e catalogos read-only.
- Diferenciar tabela origem, coluna origem, tabela referenciada e coluna referenciada.
- Nao inferir join quando a capability for apenas listagem de constraints.
- Filtrar por schema/tabela quando informado.
- Nao consultar valores de linhas para confirmar relacionamento.
- Registrar quando nao houver FKs declaradas ou permissao suficiente.
- Evitar expor comentarios sensiveis de constraints.
- A saida deve alimentar `suggest-joins` e `generate-erd-report`.
