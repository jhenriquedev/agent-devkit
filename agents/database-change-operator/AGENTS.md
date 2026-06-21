# AGENTS.md

Instrucoes especificas para agentes trabalhando em `agents/database-change-operator/`.

## Papel do agente

Este agente executa mudancas controladas em banco de dados PostgreSQL quando a
connection string local possui permissao. Ele e separado do
`postgres-data-analyzer`, que permanece read-only.

## Regras obrigatorias

- Toda escrita real exige `--execute`.
- Sempre gerar plano antes de aplicar migration ou script.
- Nunca imprimir connection string, senha ou URL completa.
- Usar `statement_timeout` e `lock_timeout`.
- Preferir transacao para scripts que permitem transacao.
- Registrar migrations aplicadas em tabela de historico.
- Bloquear comandos perigosos como `DROP DATABASE`, `DROP SCHEMA`,
  `ALTER SYSTEM`, `COPY ... PROGRAM`, `CREATE EXTENSION`, `GRANT` e `REVOKE`.
- Exigir rollback para migrations classificadas como destrutivas.

## Estrutura local

- `agent.yaml`: manifesto publico.
- `capabilities/`: casos de uso executaveis.
- `knowledge/`: contexto, politicas e prompts.
- `templates/`: modelos de saida.
- `infra/`: repository e contratos da integracao Postgres.
