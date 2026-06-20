# Knowledge

Conhecimento estavel do Azure DevOps Orchestrator.

## Objetivo

Guardar o contexto, politicas, linguagem e regras que fazem o agente decidir de
forma consistente. Esta camada e carregada pelo agente consumidor para entender
como operar o dominio antes de escolher uma capability.

## Conteudo atual

- `context.md`: contexto minimo do dominio Azure DevOps Boards.
- `policies.yaml`: politica de leitura, escrita, confirmacao e auditoria.
- `prompts/`: prompts usados pelas capabilities.

## Regras

- Coloque aqui conhecimento reutilizado por varias capabilities.
- Nao coloque ferramentas executaveis nesta camada.
- Prompts fazem parte do conhecimento operacional do agente.
- Templates de saida ficam em `../templates/`.
