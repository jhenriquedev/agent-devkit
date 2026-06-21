# Elasticsearch Integration

Repository read-only para consultar Elasticsearch via API HTTP.

## Escopo

- fontes: indices, data streams e aliases;
- mappings;
- busca de eventos;
- contagem;
- agregacoes por termo;
- timeline;
- busca por `_id`.

## Env

```env
ELASTICSEARCH_URL=
ELASTICSEARCH_API_KEY=
ELASTIC_API_KEY=
EC_API_KEY=
ELASTICSEARCH_DEFAULT_TIME_FIELD=@timestamp
```

O source de logs nao fica no `.env`; use `--source` nas capabilities.
