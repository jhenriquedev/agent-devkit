# Agent DevKit Agent Builder

Instrucoes locais para o agente `agent-devkit-agent-builder`.

## Responsabilidade

Este agente cria e valida novos agentes internos do proprio Agent DevKit em
`agents/<agent-id>/`.

## Guardrails

- Nao criar arquivos fora de `agents/<agent-id>/`.
- Nao sobrescrever agente existente sem permissao explicita.
- Nao persistir segredos, URLs privadas ou contexto de cliente.
- Nao criar provider ou dependencia externa nova.
- Gerar sempre `write_policy`, `workflow.md` e `decision-rules.md`.
- Usar dry-run como comportamento padrao para scaffold.

## Fora De Escopo

- Agentes genericos para outros projetos.
- Marketplace de agentes.
- Interface grafica.
- Geracao baseada em LLM nesta primeira versao.
