# Workflow

1. Validar schema e tabela.
2. Validar payload JSON de campos a atualizar.
3. Exigir clausula `where` especifica.
4. Sem `--execute`, retornar dry-run.
5. Com `--execute`, contar linhas afetadas antes do update e executar em transacao.
