# Workflow

1. Ler SQL local.
2. Detectar policies sobre `storage.objects`.
3. Detectar acesso publico amplo e upsert sem SELECT/UPDATE/INSERT suficientes.
4. Retornar findings read-only.
