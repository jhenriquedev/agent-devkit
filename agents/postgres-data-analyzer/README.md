# Postgres Data Analyzer

Agente especialista para analise read-only de dados em PostgreSQL.

## Escopo inicial

- testar conexao;
- listar schemas;
- listar tabelas e views;
- descrever tabela;
- executar query read-only com limite;
- gerar perfil de tabela;
- detectar colunas sensiveis;
- analisar coluna de CPF;
- gerar relatorio de dados.

## Como usar

```bash
./ai-devkit run postgres-data-analyzer test-connection
./ai-devkit run postgres-data-analyzer list-tables --schema public
./ai-devkit run postgres-data-analyzer describe-table --schema public --table customers
./ai-devkit run postgres-data-analyzer run-readonly-query --query "select * from public.customers" --limit 50
./ai-devkit run postgres-data-analyzer analyze-cpf-column --schema public --table customers --column cpf
./ai-devkit run postgres-data-analyzer list-tables --database outro_banco --schema public
```

## Configuracao

Use `.env` local:

```env
POSTGRES_DB_CONN_STRING=
```

O banco padrao vem da connection string. Quando a mesma credencial tiver acesso
a outros databases no mesmo host, use `--database <nome>` para trocar apenas o
database da URL. Schema/tabela/query/campo continuam vindo por input da
capability.
