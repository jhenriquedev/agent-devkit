# Decision Rules: Describe Table

- Consultar somente catalogos e metadados read-only da tabela.
- Validar schema e tabela antes de descrever.
- Incluir colunas, tipos, nulabilidade, defaults, PKs, FKs, indices e constraints quando disponiveis.
- Nao amostrar linhas de dados nesta capability.
- Nao expor comentarios ou defaults que contenham segredos sem mascaramento.
- Destacar colunas potencialmente sensiveis por nome, sem mostrar valores.
- Indicar quando metadados estiverem incompletos por permissao insuficiente.
- Manter a saida adequada para orientar queries futuras e ERD.
