# Prompt — Update Records

Objetivo: atualizar registros com SET JSON e WHERE específico, com preview de
impacto.

Entradas: `--schema`, `--table`, `--set-json`, `--where`; opcional `--database`,
`--execute`.

Raciocínio:
1. Valide schema/table e o WHERE (rejeite `where true`/`1=1`/multi-statement).
2. SEMPRE obtenha o preview de linhas afetadas — inclusive em dry-run (count(*)
   com o mesmo WHERE).
3. Sem `--execute`: dry-run com o preview e o plano.

Rubrica:
- WHERE amplo (`true`, `1=1`) -> RECUSE.
- affected_rows > max_affected_rows -> peça CONFIRMAÇÃO reforçada antes de
  `--execute`.
- Para mudança estrutural -> prefira migration.

Saída: affected_rows (preview), status, where, plano.

NÃO faça: não aceite WHERE amplo; não atualize sem `--execute`; não atualize um
volume grande sem confirmação; não use para DDL.
