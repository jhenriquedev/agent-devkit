# Update Incident Workflow

## Fluxo

1. Receber `--id` ou `--number`, `fields_json` e flags.
2. Parsear JSON de campos.
3. Validar campos contra operacoes unsupported.
4. Bloquear `request`, fechamento, resolucao, arquivamento e escalonamento.
5. Sem fixture, exigir alvo explicito.
6. Chamar update em dry-run por padrao.
7. Renderizar alvo, campos e proxima acao.

## Saida

Retorna `incident-update-plan.md`.
