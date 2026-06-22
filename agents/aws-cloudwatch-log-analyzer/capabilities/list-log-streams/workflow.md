# Workflow: List Log Streams

## Objetivo

Listar streams de um log group para descobrir fontes de eventos antes de
consultas mais caras ou especificas.

## Passos

1. Validar `region` e `log_group`.
2. Aplicar `log_stream_prefix` quando informado.
3. Executar `describe_log_streams`.
4. Renderizar stream, ultimo evento conhecido e bytes armazenados.

## Guardrails

- Nao consultar eventos nesta capability.
- Aplicar limite padrao e evitar descoberta ampla sem necessidade.
- Sinalizar quando nenhum prefixo de stream for informado.
