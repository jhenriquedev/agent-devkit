# Prompt: Backup Records

Objetivo: criar backup logico (snapshot JSON via `FOR JSON PATH`) das linhas
selecionadas por `WHERE`, gravado em `<schema_controle>.record_backups`.

Entradas: `--schema`, `--table`, `--where` (obrigatorios); `--execute`.

Passos:
1. Dry-run: confirme `schema`, `table`, `where_sql`.
2. Execute com `--execute`: insere payload JSON + metadados em `record_backups`.

Uso recomendado: rodar ANTES de `update-records`/`delete-records` com o mesmo
`--where` para ter rede de recuperacao.

NAO faca: backup com WHERE amplo desnecessario (custo); expor o conteudo de
`record_backups` ao usuario sem necessidade.
