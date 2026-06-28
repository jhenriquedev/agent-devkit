# Decision Rules: Describe Table

- Consultar somente catalogos e metadados read-only da tabela.
- Validar database, schema e table como identificadores seguros.
- Incluir colunas, tipos, nulabilidade, defaults, PKs, FKs, indices e constraints quando disponiveis.
- Nao amostrar linhas de dados nesta capability.
- Nao expor connection string, usuario, senha, host completo ou URL completa.
- Destacar colunas potencialmente sensiveis por nome, sem mostrar valores.
- Registrar permissao insuficiente ou metadado incompleto como lacuna.
- Aplicar `LOCK_TIMEOUT` e timeout em consultas de catalogo.
- Manter paths e nomes de objetos claros para proximas queries.
- A saida deve orientar `sample-table`, `profile-table`, `suggest-joins` e ERD.
