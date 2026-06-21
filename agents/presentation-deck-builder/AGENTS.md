# AGENTS.md

Instrucoes especificas para agentes trabalhando em
`agents/presentation-deck-builder/`.

## Papel do agente

Este agente cria, registra, versiona, refina e usa templates de apresentacao
para gerar decks PowerPoint. Ele deve tratar templates como ativos versionados,
nao como arquivos descartaveis.

## Regras obrigatorias

- Nunca sobrescrever uma versao validada de template.
- Sempre criar uma nova versao para ajustes em template validado.
- Perguntar antes de salvar template recebido em `templates/`.
- Cada template deve ter `template.yaml`, `versions/<version>/template.pptx`,
  `input-schema.xlsx`, `input-schema.md`, `slide-map.yaml` e changelog.
- Se o conteudo de entrada estiver incompleto ou ambiguo, perguntar antes de
  gerar o deck.
- Se o template estiver validado e a entrada estruturada estiver completa,
  gerar sem perguntas adicionais.
- Manter compatibilidade de paths em macOS, Windows e Linux.

## Estrutura local

- `agent.yaml`: manifesto publico.
- `capabilities/`: casos de uso acionaveis.
- `knowledge/`: contexto, politicas e catalogo de templates.
- `templates/`: templates versionados e artefatos reutilizaveis.
- `infra/`: integrações futuras para leitura de documentos e renderizacao.
