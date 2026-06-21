# AGENTS.md

Instrucoes especificas para agentes trabalhando em `agents/postgres-data-analyzer/`.

## Papel do agente

Este agente e especialista em analise read-only de dados em PostgreSQL:
descoberta de schemas, tabelas, colunas, queries, perfis de dados, campos
sensiveis e analise de CPF.

## Regras obrigatorias

- Operacoes sao read-only.
- Nunca executar `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`,
  `CREATE`, `GRANT`, `REVOKE`, `VACUUM` ou similares.
- Queries livres devem aceitar apenas `SELECT`, `WITH` ou `EXPLAIN`.
- Sempre aplicar `statement_timeout`.
- Sempre aplicar `LIMIT` automatico em queries exploratorias.
- Mascarar CPF em saidas humanas sempre que valores forem exibidos.
- Nao imprimir connection strings, usuarios, senhas ou URLs completas.

## Estrutura local

- `agent.yaml`: manifesto publico.
- `capabilities/`: casos de uso executaveis.
- `knowledge/`: contexto, politicas e prompts.
- `templates/`: modelos de saida.
- `infra/`: repository e contratos da integracao Postgres.
