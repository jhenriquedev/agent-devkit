# Workflow

1. Carregar `POSTGRES_DB_CONN_STRING` da raiz do projeto.
2. Sem `--execute`, retornar apenas o plano dos testes de permissao.
3. Com `--execute`, criar tabela temporaria, executar insert/update/delete e fazer rollback.
4. Reportar se a string de conexao permite escrita sem persistir dados.
