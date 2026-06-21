# Workflow: List Log Groups

## Objetivo

Listar log groups por regiao e prefixo para descoberta controlada.

## Passos

1. Validar `region`.
2. Aplicar `log_group_prefix` quando informado.
3. Executar `list_log_groups`.
4. Renderizar tabela com log group, retention e stored bytes.

## Guardrails

- Nao consultar eventos.
- Aplicar limite padrao.
- Avisar quando prefixo nao for informado.
