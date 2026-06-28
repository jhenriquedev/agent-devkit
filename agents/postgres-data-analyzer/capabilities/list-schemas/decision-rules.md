# Decision Rules: List Schemas

- Listar schemas apenas por catalogo read-only.
- Nao listar ou imprimir segredos de conexao.
- Separar schemas de usuario de schemas de sistema quando aplicavel.
- Respeitar permissoes; schema invisivel nao deve ser tratado como inexistente.
- Nao consultar tabelas ou dados nesta capability.
- Retornar contagem e nomes de forma estavel para automacoes.
- Usar override de database apenas como nome de banco, nunca como URL.
- Indicar proximos passos seguros para listar tabelas ou relacionamentos.
