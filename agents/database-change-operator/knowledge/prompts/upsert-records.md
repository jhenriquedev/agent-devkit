# Prompt — Upsert Records

Objetivo: inserir/atualizar registros de JSON ou CSV via
`insert ... on conflict ... do update`.

Entradas: `--schema`, `--table`, `--key-column`, `--input` (.json/.csv);
opcional `--database`, `--execute`.

Raciocínio:
1. Valide identificadores (schema/table/colunas/chave são SQL simples).
2. Confirme que a key_column existe no dataset.
3. Sem `--execute`: dry-run com record_count e plano.

Rubrica:
- record_count acima do teto de carga (max_affected_rows) -> peça confirmação;
  upsert é para cargas pequenas/controladas, não ETL massivo.
- valores são tratados como texto (limitação atual); se houver tipos
  não-textuais críticos (NULL, números, bool), avise o usuário.

Saída: record_count, status, plano.

NÃO faça: não rode sem `--execute`; não aceite identificadores complexos; não use
para volumes massivos.
