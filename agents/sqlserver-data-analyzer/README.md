# SQL Server Data Analyzer

Agente especialista para analise read-only de dados em Microsoft SQL Server.

## Escopo inicial

- testar conexao;
- listar databases, schemas, tabelas e views;
- descrever tabela, colunas, constraints e indices;
- listar relacionamentos e gerar relatorio ERD;
- procurar tabelas e colunas;
- sugerir joins;
- executar query read-only com `TOP` automatico;
- validar query antes de executar;
- criar query de analise a partir de uma pergunta;
- amostrar e perfilar tabelas;
- detectar colunas sensiveis e problemas de qualidade;
- analisar coluna de CPF;
- estimar tamanho de tabelas;
- explicar plano estimado de query;
- comparar tabelas;
- rastrear registro por relacionamentos;
- gerar relatorio de dados.

## Como usar

```bash
agent run sqlserver-data-analyzer test-connection
agent run sqlserver-data-analyzer list-tables --schema dbo
agent run sqlserver-data-analyzer describe-table --schema dbo --table Customers
agent run sqlserver-data-analyzer run-readonly-query --query "select * from dbo.Customers" --limit 50
agent run sqlserver-data-analyzer run-readonly-query --query "select * from dbo.Customers" --format json
agent run sqlserver-data-analyzer suggest-joins --schema dbo
```

## Configuracao

Use `.env` local:

```env
SQLSERVER_DB_CONN_STRING=
SQLSERVER_STATEMENT_TIMEOUT=15000
SQLSERVER_LOCK_TIMEOUT=5000
SQLSERVER_QUERY_LIMIT=100
```

O banco vem da connection string, mas database/schema/tabela/query/campo devem
vir por input da capability quando o escopo precisar ser explicito.
