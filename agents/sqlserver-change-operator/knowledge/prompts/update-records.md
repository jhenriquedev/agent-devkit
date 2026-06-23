# Prompt: Update Records

Objetivo: aplicar `UPDATE <schema>.<table> SET ... WHERE ...` com `WHERE`
obrigatorio, limite de linhas e dry-run por padrao.

Entradas (todas obrigatorias menos exec): `--schema`, `--table`, `--set-json`
(JSON de colunas->valores), `--where` (clausula estreita), `--execute`,
`--max-affected-rows` (opcional, default 100).

Passos:
1. Valide que `--where` e estreito (NUNCA `1=1`/`true`/vazio — o runner recusa).
2. Dry-run: apresente o `UPDATE` que seria gerado, `where_sql`, `max_affected_rows`.
3. Na execucao, o runner conta linhas (`count_where`) e ABORTA se exceder o limite
   (`affected rows X exceeds max_affected_rows Y`). Se o usuario quiser mais, peca
   `--max-affected-rows` explicito e justificativa.
4. Confirme; execute com `--execute`. Registra `update` em `change_audit`.

Rubrica: `set_json` vazio -> recuse (runner exige >=1 campo). Identificadores
invalidos -> recuse.

NAO faca: aceitar `WHERE` amplo; elevar limite sem justificativa do usuario.
