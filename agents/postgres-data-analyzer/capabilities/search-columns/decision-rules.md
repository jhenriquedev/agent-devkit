# Decision Rules: Search Columns

- Buscar colunas por metadados read-only do catalogo.
- Pesquisar por nome, tipo e schema sem consultar valores de linhas.
- Aplicar filtros e limites para evitar retorno massivo.
- Destacar colunas potencialmente sensiveis por nome e tipo.
- Nao inferir que coluna contem CPF/CNPJ apenas por um match fraco sem marcar baixa confianca.
- Nao expor connection strings, comentarios sensiveis ou defaults com segredo.
- Retornar schema, tabela, coluna e tipo de forma estavel para automacoes.
- A saida deve orientar `describe-table`, `analyze-cpf-column` e queries futuras.
