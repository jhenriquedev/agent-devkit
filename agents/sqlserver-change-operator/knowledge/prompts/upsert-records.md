# Prompt: Upsert Records

Objetivo: inserir-ou-atualizar registros de um arquivo JSON ou CSV por chave.

Entradas (obrigatorias): `--schema`, `--table`, `--key-column`, `--input` (caminho
.json ou .csv); `--execute`.

Passos:
1. Dry-run: o runner monta um SQL `if exists ... update ... else insert` por
   registro; apresente `record_count` e o plano.
2. Valide que `key_column` existe nas colunas do arquivo (runner recusa se nao).
3. Confirme; execute com `--execute`. Registra `upsert` em `change_audit`.

Rubrica: arquivo vazio -> recuse ("input file contains no records"). Colunas com
identificador invalido -> recuse.

NAO faca: upsert sem dry-run para cargas grandes; assumir schema das colunas.
