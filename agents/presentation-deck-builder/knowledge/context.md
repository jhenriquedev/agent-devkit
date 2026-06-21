# Presentation Deck Builder Context

Este agente gerencia templates de apresentacao e gera decks PowerPoint.

## Conceitos

- Template e um ativo versionado.
- Versao validada nunca deve ser sobrescrita.
- Ajustes em template validado criam nova versao.
- Cada template deve gerar um arquivo de entrada para o usuario preencher.

## Estrutura de template

```text
templates/<template-id>/
├─ template.yaml
├─ changelog.md
└─ versions/
   └─ <version>/
      ├─ template.pptx
      ├─ input-schema.xlsx
      ├─ input-schema.md
      ├─ slide-map.yaml
      ├─ usage-notes.md
      └─ changelog.md
```

## Modos

- Modo template: registrar, criar, versionar, refinar e validar templates.
- Modo deck: usar template + conteudo para gerar apresentacao.

## Nao assumir

- Nao inventar conteudo de negocio ausente.
- Nao trocar identidade visual de template validado sem pedido explicito.
- Nao promover versao para `current_version` sem aprovacao.
