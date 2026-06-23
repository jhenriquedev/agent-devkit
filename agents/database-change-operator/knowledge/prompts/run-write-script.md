# Prompt — Run Write Script

Objetivo: executar um script de escrita PONTUAL que não precisa virar migration
versionada.

Entradas: `--path`; opcional `--database`, `--execute`.

Raciocínio:
1. Planeje (checksum, operações, blocked, destructive, transactional).
2. Sem `--execute`: dry-run.
3. Se a mudança precisa de histórico permanente -> recomende migration em vez de
   script.

Rubrica:
- plan.blocked == yes -> RECUSE.
- plan.destructive == yes -> exija CONFIRMAÇÃO DESTRUTIVA reforçada do usuário
  antes de `--execute` (DROP/TRUNCATE/DELETE sem WHERE deixam trilha?).
- não transacional -> avise antes.

Saída: status e plano.

NÃO faça: não execute bloqueado; não rode destrutivo sem confirmação explícita;
não use script para algo que deveria ser migration auditável.
