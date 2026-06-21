# Contexto

- O agente opera PostgreSQL apenas em modo read-only.
- A connection string fica em `POSTGRES_DB_CONN_STRING` e define o banco padrao.
- O input opcional `--database` troca apenas o database da URL base, mantendo host, porta, usuario, senha e SSL.
- Schema, tabela, coluna e query devem vir por input da capability.
- Saidas humanas devem evitar dumps de dados pessoais.
- CPFs exibidos devem ser mascarados.
- Relatorios devem separar dados coletados de inferencias.
