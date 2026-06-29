# Workflow

1. Validar spec com `plan-desktop-automation`.
2. Exigir `target_project` para escrita.
3. Em dry-run, retornar arquivos planejados sem escrever.
4. Com `--execute`, escrever somente dentro de `target_project`.
5. Bloquear overwrite sem `--allow-overwrite`.
