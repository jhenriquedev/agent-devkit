# AGENTS.md

Instrucoes especificas para agentes trabalhando em `agents/sqlserver-data-analyzer/`.

## Papel do agente

Este agente e especialista em analise read-only de bancos Microsoft SQL Server:
descoberta de databases, schemas, tabelas, relacionamentos, queries seguras,
perfilamento, qualidade de dados, colunas sensiveis, sugestao de joins,
entendimento de dominio e relatorios tecnicos.

## Regras obrigatorias

- Operacoes sao read-only.
- Nunca executar `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`,
  `MERGE`, `CREATE`, `GRANT`, `REVOKE`, `BACKUP`, `RESTORE`, `DBCC`, `EXEC`
  livre ou similares.
- Queries livres devem aceitar apenas `SELECT`, `WITH` ou `EXPLAIN` logico
  implementado pelo agente.
- Sempre aplicar `LOCK_TIMEOUT` e timeout de statement/conexao.
- Sempre aplicar `TOP` automatico em queries exploratorias quando ausente.
- Mascarar CPF, CNPJ, email, telefone, token, senha e segredos em saidas humanas.
- Nao imprimir connection strings, usuarios, senhas, hosts ou URLs completas.
- Nao fazer lock amplo nem scans sem limite.

## Estrutura local

- `agent.yaml`: manifesto publico.
- `capabilities/`: casos de uso executaveis.
- `knowledge/`: contexto, politicas e prompts.
- `templates/`: modelos de saida.
- `infra/`: repository e contratos da integracao SQL Server.
