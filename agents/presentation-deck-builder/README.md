# Presentation Deck Builder

Agente especialista em criar, versionar e reutilizar templates de apresentacao
para gerar arquivos PowerPoint.

## Escopo inicial

- registrar templates `.pptx` recebidos;
- versionar templates sem sobrescrever versoes validadas;
- gerar arquivos de entrada para preenchimento pelo usuario;
- listar templates e versoes;
- planejar decks a partir de documentos de entrada;
- gerar decks PowerPoint a partir de template e conteudo estruturado;
- revisar e refinar decks gerados.

## Como usar

```bash
agent capabilities presentation-deck-builder
agent run presentation-deck-builder register-template --template status.pptx --template-id status-report --version 0.1.0 --yes-save
agent run presentation-deck-builder list-template-versions --template-id status-report
```

Templates ficam em:

```text
agents/presentation-deck-builder/templates/<template-id>/
```

Cada template tem versoes em:

```text
templates/<template-id>/versions/<version>/
```

## Versionamento

- `patch`: ajustes pequenos de texto, espacamento ou placeholders.
- `minor`: novo slide/layout ou mudanca no input schema.
- `major`: mudanca incompatível no template ou no arquivo de entrada.

Versoes podem ter status `draft`, `validated`, `deprecated` ou `archived`.
