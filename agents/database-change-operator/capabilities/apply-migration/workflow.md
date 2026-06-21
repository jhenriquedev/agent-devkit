# Workflow

1. Planejar a migration.
2. Sem `--execute`, retornar dry-run com checksum e operacoes.
3. Com `--execute`, garantir a tabela `ai_devkit_migrations`.
4. Verificar se o mesmo ID ja foi aplicado.
5. Bloquear checksum divergente para migration ja aplicada.
6. Aplicar SQL e registrar historico.
