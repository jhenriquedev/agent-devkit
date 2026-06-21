# AGENTS.md

Instrucoes especificas para agentes trabalhando em `agents/sqlserver-change-operator/`.

## Papel do agente

Este agente executa mudancas controladas em Microsoft SQL Server quando a
connection string local possui permissao. Ele e separado do
`sqlserver-data-analyzer`, que permanece read-only.

## Regras obrigatorias

- Toda escrita real exige `--execute`.
- Sempre gerar plano antes de aplicar migration ou script.
- Nunca imprimir connection string, senha, host completo ou URL completa.
- Usar `XACT_ABORT ON`, `LOCK_TIMEOUT` e timeout de statement/conexao.
- Preferir transacao para scripts que permitem transacao.
- Registrar migrations e mudancas em tabelas de historico no schema configurado.
- `UPDATE` e `DELETE` exigem `WHERE` explicito.
- `DELETE` real exige `--confirm-delete`.
- Operacoes acima do limite exigem `--max-affected-rows` explicito.
- Bloquear `DROP DATABASE`, `ALTER SERVER`, `ALTER LOGIN`, `CREATE LOGIN`,
  `GRANT`, `REVOKE`, `BACKUP DATABASE`, `RESTORE`, `TRUNCATE`, `xp_cmdshell`,
  `sp_configure`, `OPENROWSET` e linked servers.
- Exigir rollback para migrations classificadas como destrutivas.

## Estrutura local

- `agent.yaml`: manifesto publico.
- `capabilities/`: casos de uso executaveis.
- `knowledge/`: contexto, politicas e prompts.
- `templates/`: modelos de saida.
- `infra/`: repository e contratos da integracao SQL Server.
