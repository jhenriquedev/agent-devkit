# Workflow: Detect Error Patterns

## Objetivo

Agrupar eventos de erro para identificar recorrencia.

## Passos

1. Validar escopo.
2. Buscar eventos.
3. Filtrar eventos de erro quando necessario.
4. Agrupar por `message`, `status_code`, `endpoint` ou `stream`.
5. Renderizar frequencia e exemplos.

## Guardrails

- Aplicar limite.
- Nao tratar mensagens parecidas como iguais sem normalizacao.
- Mostrar exemplos curtos.
