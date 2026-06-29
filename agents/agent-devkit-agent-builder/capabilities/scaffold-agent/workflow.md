# Workflow

1. Ler a spec YAML ou JSON.
2. Gerar plano de arquivos.
3. Em dry-run, retornar os arquivos planejados sem escrever.
4. Com `--execute`, escrever apenas dentro de `agents/<agent-id>/`.
5. Bloquear overwrite sem `--allow-overwrite`.
6. Retornar arquivos escritos e proximos passos de validacao.
