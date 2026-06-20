# Scripts

Esta pasta contem automacoes operacionais do repositorio AI DevKit como um todo.

## Objetivo

Guardar scripts globais que atuam sobre varios agentes ou sobre o ciclo de vida
do repositorio.

## Exemplos

- Validar todos os `agent.yaml`.
- Gerar catalogos globais a partir dos manifests dos agentes.
- Rodar checagens de consistencia em todos os agentes.
- Empacotar agentes para distribuicao.

## Regras

- Nao coloque scripts especializados de dominio aqui.
- Integracoes executaveis de um agente devem ficar em
  `agents/<agent-id>/infra/integrations/<provider>/`.
- Runners de capabilities devem ficar na propria capability e ser declarados em
  `capability.yaml`.
- Se uma automacao nao atua sobre o repositorio inteiro, ela provavelmente nao
  pertence a esta pasta.
