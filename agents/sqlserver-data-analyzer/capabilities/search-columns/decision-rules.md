# Decision Rules: Search Columns

- Buscar colunas por metadados read-only do catalogo.
- Pesquisar por nome, tipo, schema e tabela sem consultar valores de linhas.
- Aplicar filtros e limites para evitar retorno massivo.
- Destacar colunas potencialmente sensiveis por nome e tipo.
- Nao inferir CPF/CNPJ por match fraco sem marcar baixa confianca.
- Nao expor connection string, comentarios sensiveis ou defaults com segredo.
- Aplicar timeout e `LOCK_TIMEOUT`.
- Retornar database, schema, tabela, coluna e tipo de forma estavel.
- A saida deve orientar `describe-table`, `analyze-cpf-column` e queries futuras.
- Nao executar `EXEC` livre nem comandos administrativos de catalogo.
