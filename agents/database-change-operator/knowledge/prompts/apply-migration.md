# Prompt — Apply Migration

Objetivo: aplicar UMA migration com confirmação explícita e histórico.

Entradas: `--path` (`.up.sql`); opcional `--name`, `--database`, `--execute`.

Raciocínio:
1. Sempre planeje primeiro (chame plan-migration ou leia o plano embutido).
2. Confirme o `Target database` com o usuário.
3. Sem `--execute`: entregue o dry-run e peça confirmação.

Rubrica de decisão:
- plan.blocked == yes -> RECUSE; não há flag que destrave.
- plan.destructive == yes && sem rollback_path -> RECUSE até existir `.down.sql`.
- migration_id já aplicado com checksum diferente -> RECUSE (drift); peça revisão.
- migration_id já aplicado com mesmo checksum -> informe "already applied", não
  reaplique.
- tudo ok + usuário confirmou -> aplique com `--execute`.

Saída: ID, status, already_applied e o plano. Confirme registro em
`ai_devkit_migrations`.

NÃO faça: não aplique sem `--execute`; não reaplique drift; não invente rollback;
não vaze conexão.
