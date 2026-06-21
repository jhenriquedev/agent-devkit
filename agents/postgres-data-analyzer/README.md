# Postgres Data Analyzer

Agente especialista para analise read-only de dados em PostgreSQL.

## Escopo inicial

- testar conexao;
- listar databases acessiveis;
- listar schemas;
- listar tabelas e views;
- descrever tabela;
- listar relacionamentos;
- sugerir joins;
- buscar tabelas e colunas;
- explorar dominio funcional do banco;
- gerar relatorio ERD;
- executar query read-only com limite;
- validar query read-only sem executar;
- montar query de analise;
- explicar plano de query;
- amostrar tabela;
- gerar perfil de tabela;
- analisar resultado de query;
- detectar colunas sensiveis;
- detectar problemas de qualidade de dados;
- analisar coluna de CPF;
- estimar tamanho de tabelas;
- comparar tabelas;
- rastrear registro por relacionamentos;
- gerar relatorio de dados.

## Como usar

```bash
./ai-devkit run postgres-data-analyzer test-connection
./ai-devkit run postgres-data-analyzer list-tables --schema public
./ai-devkit run postgres-data-analyzer describe-table --schema public --table customers
./ai-devkit run postgres-data-analyzer run-readonly-query --query "select * from public.customers" --limit 50
./ai-devkit run postgres-data-analyzer suggest-joins --schema public
./ai-devkit run postgres-data-analyzer generate-erd-report --schema public
./ai-devkit run postgres-data-analyzer analyze-cpf-column --schema public --table customers --column cpf
./ai-devkit run postgres-data-analyzer list-tables --database outro_banco --schema public
```

## Configuracao

Use `.env` local:

```env
POSTGRES_DB_CONN_STRING=
POSTGRES_STATEMENT_TIMEOUT=15000
POSTGRES_QUERY_LIMIT=100
```

O banco padrao vem da connection string. Quando a mesma credencial tiver acesso
a outros databases no mesmo host, use `--database <nome>` para trocar apenas o
database da URL. Schema/tabela/query/campo continuam vindo por input da
capability.
