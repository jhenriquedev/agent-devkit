# Prompt: Delete Records

Objetivo: `DELETE <schema>.<table> WHERE ...` com `WHERE` obrigatorio, limite e
DUPLA confirmacao (`--execute` E `--confirm-delete`).

Entradas: `--schema`, `--table`, `--where` (obrigatorios); `--execute`,
`--confirm-delete` (ambos para apagar de verdade); `--max-affected-rows` (opcional).

Passos:
1. Dry-run: apresente o `DELETE` e o `where_sql`. Deixe claro que e destrutivo.
2. Lembre: a execucao real exige `--execute` E `--confirm-delete`; sem o segundo, o
   runner falha em preflight ("--confirm-delete is required").
3. Conte/estime linhas; respeite `max_affected_rows`.
4. Sugira `backup-records` com o MESMO `--where` ANTES de apagar (boa pratica).
5. Confirme com o usuario; execute. Registra `delete` em `change_audit`.

NAO faca: deletar sem WHERE estreito; deletar sem oferecer backup; ignorar o limite.
