# Prompt: Create Object

Objetivo: criar objeto (tabela, view, proc, etc.) a partir de SQL revisado. O
runner EXIGE que o script contenha ao menos um statement `CREATE`.

Entradas: `--path` (obrigatorio); `--execute`.

Passos:
1. Dry-run: confirme que ha statement `CREATE` (senao o runner recusa) e apresente
   o plano.
2. `blocked: yes` -> PARE.
3. Confirme; execute com `--execute`.

NAO faca: usar esta capability para DML/UPDATE/DELETE (use a capability propria);
criar login/objeto de servidor (bloqueado).
