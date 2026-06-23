# Prompt — Rollback Migration

Objetivo: reverter uma migration a partir de um `.down.sql` real.

Entradas: `--path` (`.down.sql`); opcional `--database`, `--execute`.

Raciocínio:
1. Planeje o `.down.sql` (rollback também passa por classificação de risco).
2. Sem `--execute`: dry-run e confirmação.
3. Com `--execute`: execute em transação e marque o histórico como
   `rolled_back`.

Rubrica:
- Se o `.down.sql` não existir ou não for `.down.sql` -> pare e peça o arquivo
  correto. Nunca gere rollback automático.
- Se o rollback falhar -> retorne o erro do psql como veio (não esconda stderr).

Saída: migration_id, status `rolled_back`, plano.

NÃO faça: não invente rollback; não silencie erro de psql; não rode sem
`--execute`.
