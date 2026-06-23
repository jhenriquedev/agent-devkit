# Prompt: Apply Migration

Objetivo: aplicar UMA migration com historico e checksum, dry-run por padrao.

Entradas: `--path` (obrigatorio); `--rollback-path` (obrigatorio se destrutiva);
`--name` (opcional, rotulo no historico); `--execute` (para aplicar de verdade).

Passos de raciocinio:
1. Rode primeiro em dry-run (sem `--execute`). Apresente o plano.
2. Se `blocked: yes` -> PARE, nao ofereca execucao.
3. Se `destructive: yes` e sem `rollback_path` -> exija `--rollback-path` (arquivo
   `.down.sql`) antes de continuar.
4. Peca confirmacao explicita do usuario.
5. Execute com `--execute`. O agente checa idempotencia por `migration_id` +
   `checksum`: se ja aplicada com mesmo checksum, retorna `already_applied`; se
   checksum diferente, FALHA ("already applied with different checksum") — nesse
   caso, NAO force; investigue divergencia com o usuario.

Regras de decisao / rubrica:
- risco `high` -> confirmacao forte.
- Sempre registrar em `change_audit` (automatico).

Saida: resultado com `status`, `migration_id`, plano. NAO faca: reexecutar migration
com checksum divergente; aplicar sem dry-run previo.
