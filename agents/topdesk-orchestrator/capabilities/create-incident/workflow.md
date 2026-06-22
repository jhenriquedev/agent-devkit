# Create Incident Workflow

## Fluxo

1. Receber `brief_description`, `request` e campos opcionais.
2. Mesclar `fields_json` com argumentos explicitos.
3. Exigir resumo e request.
4. Montar payload minimo.
5. Sem `--execute`, chamar repository em dry-run.
6. Com `--execute`, criar incidente.
7. Renderizar payload planejado e resultado.

## Guardrails

- Nao criar incidente sem resumo e request.
- Escrita real exige `--execute`.

## Saida

Retorna `incident-create-plan.md`.
