# Postgres Integration

Repository read-only para PostgreSQL usando `psql`.

## Env

```env
POSTGRES_DB_CONN_STRING=
POSTGRES_STATEMENT_TIMEOUT=15000
```

Queries sao enviadas ao `psql` por stdin. Quando a connection string esta no
formato URL, o repository converte para variaveis `PG*` para evitar passar a
senha como argumento de processo.
