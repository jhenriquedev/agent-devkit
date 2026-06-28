# Decision Rules: List Databases

- Listar databases apenas por catalogo read-only acessivel ao usuario.
- Nao aceitar connection string, path ou SQL como nome de database.
- Nao imprimir connection string, usuario, senha, host completo ou URL completa.
- Filtrar ou marcar databases de sistema quando isso reduzir ruido operacional.
- Respeitar permissao; database invisivel nao deve ser tratado como inexistente.
- Nao conectar automaticamente em todos os databases listados.
- Aplicar timeout e `LOCK_TIMEOUT` nas consultas de catalogo.
- Retornar database atual, quantidade e nomes de forma estavel.
- Nao executar perfilamento ou amostragem nesta capability.
- A saida deve orientar selecao segura para capabilities seguintes.
