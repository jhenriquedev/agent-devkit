# Workflow

1. Validar spec com `plan-lambda`.
2. Exigir `target_project` existente.
3. Em dry-run, retornar arquivos planejados.
4. Com `--execute`, escrever somente dentro de `target_project`.
5. Bloquear overwrite sem `--allow-overwrite`.
