# Contexto

- O agente opera SQL Server apenas em modo read-only.
- A connection string fica em `SQLSERVER_DB_CONN_STRING`.
- Database, schema, tabela, coluna e query devem vir por input da capability
  quando o escopo precisar ser explicito.
- Saidas humanas devem evitar dumps de dados pessoais.
- CPFs, CNPJs, emails, telefones, tokens e segredos exibidos devem ser
  mascarados.
- Relatorios devem separar dados coletados de inferencias.
- Sugestoes de join podem vir de constraints reais ou heuristicas por nome/tipo.
