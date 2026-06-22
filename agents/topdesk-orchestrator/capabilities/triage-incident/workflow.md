# Triage Incident Workflow

## Fluxo

1. Receber `--id` ou `--number`, ou carregar fixture com `incident`.
2. Ler o incidente TOPdesk.
3. Carregar catalogos de categorias e prioridades.
4. Buscar pessoa correspondente ao solicitante quando houver nome.
5. Aplicar `knowledge/triage-rules.md`.
6. Sugerir apenas valores presentes nos catalogos carregados.
7. Montar payload minimo de update com categoria, prioridade e caller.
8. Validar campos contra operacoes unsupported.
9. Sem `--execute`, retornar somente dry-run.
10. Com `--execute`, aplicar update e relatar resultado.

## Saida

Retorna `incident-triage-plan.md` com fatos, inferencias e plano de update.
