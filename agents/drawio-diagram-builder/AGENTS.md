# AGENTS.md

Instrucoes especificas para agentes trabalhando em
`agents/drawio-diagram-builder/`.

## Papel do agente

Este agente e especialista em criar, revisar e refinar diagramas editaveis em
Draw.io/diagrams.net a partir de documentos, pastas, cards, specs, inventarios,
briefings e feedback iterativo.

## Regras obrigatorias

- Gerar artefatos `.drawio` editaveis, nao apenas imagens.
- Separar fatos observados, inferencias, premissas e perguntas abertas.
- Fazer entrevista objetiva quando o material nao definir objetivo, audiencia,
  escopo, nivel de detalhe ou fluxo esperado.
- Recomendar multiplos diagramas quando um unico diagrama ficaria poluido.
- Preservar rastreabilidade entre fonte, spec intermediaria e elementos do
  diagrama.
- Validar XML, referencias de conectores, labels e geometria antes de declarar
  entrega concluida.
- Nao depender de servicos externos para renderizar o `.drawio`.
- Delegar leitura de cards Azure ao `azure-devops-orchestrator` quando o
  contexto vier de Azure DevOps.
- Consultar `vendor/skills/drawio-diagramming` para regras de formato,
  layout e qualidade quando trabalhar com `.drawio`.

## Estrutura local

- `agent.yaml`: manifesto publico.
- `capabilities/`: casos de uso acionaveis pela CLI.
- `knowledge/`: contexto, politicas e taxonomia de diagramas.
- `templates/`: schemas, presets e bibliotecas de shapes.
- `infra/integrations/drawio/`: renderer, leitores e validadores locais.
