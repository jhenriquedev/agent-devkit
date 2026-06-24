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

Configure segredos locais em `.env.local`; `.env` e usado apenas como fallback
para valores nao definidos.

```env
ELASTICSEARCH_URL=
ELASTICSEARCH_API_KEY=
ELASTIC_API_KEY=
EC_API_KEY=
ELASTICSEARCH_DEFAULT_TIME_FIELD=@timestamp
ELASTICSEARCH_ACCESS_MODE=cloud-proxy
ELASTICSEARCH_CLOUD_PROXY=true
ELASTICSEARCH_CLOUD_API_BASE_URL=https://api.elastic-cloud.com
ELASTICSEARCH_CLOUD_DEPLOYMENT_ID=
ELASTICSEARCH_CLOUD_RESOURCE_REF_ID=
```

Quando `ELASTICSEARCH_ACCESS_MODE=cloud-proxy` ou `ELASTICSEARCH_CLOUD_PROXY=true`,
as chamadas incluem `X-Management-Request: true`. Se `ELASTICSEARCH_URL` estiver
vazio, a URL base e derivada das variaveis `ELASTICSEARCH_CLOUD_*`.

O source de logs nao fica no `.env`; use `--source` nas capabilities.
