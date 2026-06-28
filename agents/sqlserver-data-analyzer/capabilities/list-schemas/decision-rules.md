# Decision Rules: List Schemas

- Listar schemas apenas por catalogo read-only.
- Nao listar ou imprimir segredos de conexao.
- Separar schemas de usuario de schemas de sistema quando aplicavel.
- Respeitar permissoes; schema invisivel nao deve ser tratado como inexistente.
- Nao consultar tabelas ou dados nesta capability.
- Aplicar timeout e `LOCK_TIMEOUT`.
- Retornar contagem e nomes de forma estavel para automacoes.
- Nao aceitar valores de database com caracteres de SQL ou path.
- Indicar proximos passos seguros para listar tabelas ou relacionamentos.
- A saida deve ser curta e sem dados de negocio.
