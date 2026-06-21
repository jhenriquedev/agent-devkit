# Elasticsearch Log Analyzer

Agente especialista para analisar logs em Elasticsearch.

## Escopo inicial

O MVP cobre analise read-only:

- listar fontes de logs;
- inspecionar mappings de uma fonte;
- buscar eventos por filtros explicitos;
- analisar erros de servicos;
- rastrear requests por identificador;
- detectar padroes de erro;
- extrair amostras de logs;
- gerar relatorio operacional;
- correlacionar card Azure DevOps com evidencias em logs.

## Como usar

```bash
./ai-devkit run elasticsearch-log-analyzer list-log-sources --pattern "logs-*"
./ai-devkit run elasticsearch-log-analyzer search-log-events --source "logs-prod-*" --from "now-2h" --to "now" --service "checkout-api" --level error
./ai-devkit run elasticsearch-log-analyzer trace-request --source "logs-prod-*" --request-id "abc-123" --from "now-24h" --to "now"
./ai-devkit run elasticsearch-log-analyzer generate-log-report --source "logs-prod-*" --from "now-6h" --to "now" --service "checkout-api"
```

O `.env` guarda credenciais e endpoint. O indice, servico, ambiente e periodo
devem ser informados por comando.

## Configuracao

Variaveis aceitas:

- `ELASTICSEARCH_URL`
- `ELASTICSEARCH_API_KEY`
- `ELASTIC_API_KEY`
- `EC_API_KEY`
- `ELASTICSEARCH_DEFAULT_TIME_FIELD`

`EC_API_KEY` foi mantida porque e o nome usado pelo ambiente Elastic encontrado
no shell local. Para chamadas diretas ao Elasticsearch, prefira configurar
`ELASTICSEARCH_URL` e `ELASTICSEARCH_API_KEY`.
