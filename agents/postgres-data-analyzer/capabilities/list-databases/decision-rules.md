# Decision Rules: List Databases

- Listar bancos apenas por metadados read-only acessiveis ao usuario.
- Nao aceitar URL ou connection string como override de nome de database.
- Nao imprimir host, usuario, senha, porta completa ou connection string.
- Filtrar templates e bancos de sistema quando isso reduzir ruido operacional.
- Registrar banco atual e quantidade de bancos retornados quando disponivel.
- Nao tentar conectar automaticamente em todos os bancos listados.
- Respeitar permissoes; banco invisivel nao deve ser tratado como inexistente.
- Usar esta capability para descoberta, nao para perfilamento de dados.
