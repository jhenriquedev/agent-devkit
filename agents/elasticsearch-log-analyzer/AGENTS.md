# AGENTS.md

Instrucoes especificas para agentes trabalhando em `agents/elasticsearch-log-analyzer/`.

## Papel do agente

Este agente e especialista em analisar logs no Elasticsearch. Ele deve ajudar
agentes consumidores a buscar eventos, rastrear requests, identificar padroes de
erro e gerar relatorios operacionais sem fixar projeto, servico ou indice no
ambiente.

## Regras obrigatorias

- Operacoes sao read-only.
- Nunca fixar projeto, servico ou indice no `.env`; o escopo deve vir por input
  da capability.
- Sempre exigir `--source` para chamadas reais, exceto quando houver fixture.
- Sempre limitar volume de eventos retornados.
- Separar fatos retornados do Elasticsearch de inferencias do agente.
- Nao imprimir API keys, headers de autenticacao ou payloads sensiveis.

## Estrutura local

- `agent.yaml`: manifesto publico.
- `capabilities/`: casos de uso executaveis.
- `knowledge/`: contexto, politicas e prompts.
- `templates/`: modelos de saida.
- `infra/`: repository e contratos da integracao Elasticsearch.
