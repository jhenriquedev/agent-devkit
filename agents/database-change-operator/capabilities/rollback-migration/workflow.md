# Workflow

1. Ler o arquivo rollback `.down.sql`.
2. Planejar comandos e riscos.
3. Sem `--execute`, retornar dry-run.
4. Com `--execute`, executar rollback com timeouts.
5. Atualizar historico como `rolled_back`.
