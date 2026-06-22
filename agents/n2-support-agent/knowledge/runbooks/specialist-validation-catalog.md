# Catalogo de Validacoes Especialistas N2

## Objetivo

Definir quando uma validacao especialista pode ser executada e quando deve ficar
planejada ou pulada com lacuna explicita.

## BPO

- Agente: `bpo-analyser`.
- Capabilities: `analyze-proposal`, `find-latest-proposal-by-cpf`.
- Execucao segura: `analyze-proposal` exige `proposalNumber`.
- CPF mascarado nunca deve ser enviado como parametro de busca.

## Logs Elasticsearch

- Agente: `elasticsearch-log-analyzer`.
- Capability: `search-log-events`.
- Execucao segura exige `source`, `from_time` e `to_time`.
- `query`, `service`, `environment`, `level` e `limit` sao opcionais.

## Logs CloudWatch

- Agente: `aws-cloudwatch-log-analyzer`.
- Capability: `search-log-events`.
- Execucao segura exige `region`, `log_group`, `start_time` e `end_time`.
- `filter_pattern`, `log_stream_prefix` e `limit` sao opcionais.

## Banco

- Agentes: `postgres-data-analyzer`, `sqlserver-data-analyzer`.
- Capability: `run-readonly-query`.
- Execucao segura exige query read-only explicita em `readonly_query`,
  `postgres_query`, `sqlserver_query`, `sql_query` ou `database_query`.
- `query` generica pertence a logs e nao deve ser reutilizada como SQL.
- Mutacoes ficam fora do N2.

## N1

- Agente: `n1-support-agent`.
- Capability: `execute-n1-card-runbook`.
- Execucao segura exige `project` e `card`.
- Usar quando o handoff estiver ausente, incompleto ou com diagnostic gaps
  bloqueantes.
