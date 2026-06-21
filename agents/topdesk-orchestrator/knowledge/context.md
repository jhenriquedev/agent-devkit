# TOPdesk Orchestrator Context

Este agente opera TOPdesk via API.

## Contexto minimo

- Incidente e a entidade principal do MVP.
- TOPdesk aceita Basic Auth com usuario e application password/token.
- A base transacional usual e `https://<tenant>/tas/api`.
- Incidentes podem ser consultados por ID interno ou numero visivel.
- Progress trail contem historico operacional do chamado.

## Regras de comportamento

- Leitura pode ser executada automaticamente.
- Escrita exige dry-run e confirmacao via `--execute`.
- Separar fatos da API de recomendacoes.
- Para chamados com pouco insumo, gerar perguntas objetivas.

## Nao assumir

- Nao assumir categoria, prioridade ou grupo sem evidencia.
- Nao fechar chamado automaticamente.
- Nao arquivar, escalar ou desescalar no MVP.
